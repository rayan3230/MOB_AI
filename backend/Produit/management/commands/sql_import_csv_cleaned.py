from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Fast SQL import from folder_data/csv_cleaned using PostgreSQL COPY"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv-dir",
            default="folder_data/csv_cleaned",
            help="Directory containing cleaned CSV files",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Truncate target tables before import",
        )

    def handle(self, *args, **options):
        csv_dir = Path(options["csv_dir"])
        if not csv_dir.is_absolute():
            csv_dir = Path.cwd() / csv_dir

        required_files = {
            "produits": csv_dir / "produits.csv",
            "utilisateurs": csv_dir / "utilisateurs.csv",
            "transactions": csv_dir / "transactions.csv",
            "lignes_transaction": csv_dir / "lignes_transaction.csv",
            "historique_demande": csv_dir / "historique_demande.csv",
        }

        missing = [name for name, path in required_files.items() if not path.exists()]
        if missing:
            raise CommandError(f"Missing CSV files: {', '.join(missing)} in {csv_dir}")

        if connection.vendor != "postgresql":
            raise CommandError("This command is built for PostgreSQL only.")

        self.stdout.write(f"Using CSV folder: {csv_dir}")

        with transaction.atomic():
            with connection.cursor() as cursor:
                if options.get("truncate"):
                    self.stdout.write("Truncating target tables...")
                    cursor.execute(
                        """
                        TRUNCATE TABLE
                            lignes_transaction,
                            historique_demande,
                            transactions,
                            produit,
                            utilisateurs
                        RESTART IDENTITY CASCADE
                        """
                    )

                self._import_users(cursor, required_files["utilisateurs"])
                self._import_products(cursor, required_files["produits"])
                self._import_transactions(cursor, required_files["transactions"])
                self._import_transaction_lines(cursor, required_files["lignes_transaction"])
                self._import_demand_history(cursor, required_files["historique_demande"])

                self.stdout.write("\nRow counts after import:")
                for table in ["utilisateurs", "produit", "transactions", "lignes_transaction", "historique_demande"]:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"- {table}: {count}")

        self.stdout.write(self.style.SUCCESS("SQL import completed."))

    def _copy_into_staging(self, cursor, csv_path, staging_table, columns):
        cursor.execute(f"DROP TABLE IF EXISTS {staging_table}")
        column_defs = ", ".join([f"{col} TEXT" for col in columns])
        cursor.execute(f"CREATE TEMP TABLE {staging_table} ({column_defs})")

        copy_sql = (
            f"COPY {staging_table} ({', '.join(columns)}) "
            "FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',', QUOTE '\"')"
        )
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
            if hasattr(cursor, "copy_expert"):
                cursor.copy_expert(copy_sql, handle)
            else:
                raise CommandError("Database cursor does not support copy_expert.")

    def _import_users(self, cursor, csv_path):
        self.stdout.write("Importing utilisateurs...")
        cols = [
            "id_utilisateur",
            "password",
            "nom_complet",
            "role",
            "email",
            "telephone",
            "adresse",
            "actif",
            "is_banned",
        ]
        self._copy_into_staging(cursor, csv_path, "stg_utilisateurs", cols)

        cursor.execute(
            """
            INSERT INTO utilisateurs
                (id_utilisateur, password, nom_complet, role, email, telephone, adresse, actif, is_banned)
            SELECT
                NULLIF(TRIM(id_utilisateur), ''),
                COALESCE(NULLIF(TRIM(password), ''), 'ChangeMe123!'),
                COALESCE(NULLIF(TRIM(nom_complet), ''), 'Unknown User'),
                UPPER(COALESCE(NULLIF(TRIM(role), ''), 'EMPLOYEE')),
                NULLIF(TRIM(email), ''),
                NULLIF(TRIM(telephone), ''),
                NULLIF(TRIM(adresse), ''),
                CASE WHEN LOWER(COALESCE(TRIM(actif), 'true')) IN ('1','true','t','yes','y','oui') THEN TRUE ELSE FALSE END,
                CASE WHEN LOWER(COALESCE(TRIM(is_banned), 'false')) IN ('1','true','t','yes','y','oui') THEN TRUE ELSE FALSE END
            FROM stg_utilisateurs
            WHERE NULLIF(TRIM(id_utilisateur), '') IS NOT NULL
            ON CONFLICT (id_utilisateur) DO UPDATE SET
                password = EXCLUDED.password,
                nom_complet = EXCLUDED.nom_complet,
                role = EXCLUDED.role,
                email = EXCLUDED.email,
                telephone = EXCLUDED.telephone,
                adresse = EXCLUDED.adresse,
                actif = EXCLUDED.actif,
                is_banned = EXCLUDED.is_banned
            """
        )

    def _import_products(self, cursor, csv_path):
        self.stdout.write("Importing produit...")
        cols = ["id_produit", "sku", "nom_produit", "unite_mesure", "categorie", "actif"]
        self._copy_into_staging(cursor, csv_path, "stg_produit", cols)

        cursor.execute(
            """
            INSERT INTO produit
                (id_produit, sku, nom_produit, unite_mesure, categorie, actif, collisage_palette, collisage_fardeau, poids, id_rack)
            SELECT
                NULLIF(TRIM(id_produit), ''),
                NULLIF(TRIM(sku), ''),
                COALESCE(NULLIF(TRIM(nom_produit), ''), 'Unnamed Product'),
                COALESCE(NULLIF(TRIM(unite_mesure), ''), 'Unité(s)'),
                COALESCE(NULLIF(TRIM(categorie), ''), 'MISC'),
                CASE WHEN LOWER(COALESCE(TRIM(actif), 'true')) IN ('1','true','t','yes','y','oui') THEN TRUE ELSE FALSE END,
                0,
                0,
                0,
                NULL
            FROM stg_produit
            WHERE NULLIF(TRIM(id_produit), '') IS NOT NULL
              AND NULLIF(TRIM(sku), '') IS NOT NULL
            ON CONFLICT (id_produit) DO UPDATE SET
                sku = EXCLUDED.sku,
                nom_produit = EXCLUDED.nom_produit,
                unite_mesure = EXCLUDED.unite_mesure,
                categorie = EXCLUDED.categorie,
                actif = EXCLUDED.actif
            """
        )

    def _import_transactions(self, cursor, csv_path):
        self.stdout.write("Importing transactions...")
        cols = [
            "id_transaction",
            "type_transaction",
            "reference_transaction",
            "cree_le",
            "cree_par_id_utilisateur",
            "statut",
            "notes",
        ]
        self._copy_into_staging(cursor, csv_path, "stg_transactions", cols)

        cursor.execute(
            """
            INSERT INTO transactions
                (id_transaction, type_transaction, reference_transaction, cree_le, cree_par_id_utilisateur, statut, notes)
            SELECT
                NULLIF(TRIM(s.id_transaction), ''),
                CASE UPPER(COALESCE(NULLIF(TRIM(s.type_transaction), ''), 'ISSUE'))
                    WHEN 'DELIVERY' THEN 'ISSUE'
                    ELSE UPPER(COALESCE(NULLIF(TRIM(s.type_transaction), ''), 'ISSUE'))
                END,
                COALESCE(NULLIF(TRIM(s.reference_transaction), ''), NULLIF(TRIM(s.id_transaction), '')),
                COALESCE(NULLIF(TRIM(s.cree_le), '')::timestamp, NOW()),
                u.id_utilisateur,
                CASE UPPER(COALESCE(NULLIF(TRIM(s.statut), ''), 'CONFIRMED'))
                    WHEN 'VALIDATED' THEN 'CONFIRMED'
                    ELSE UPPER(COALESCE(NULLIF(TRIM(s.statut), ''), 'CONFIRMED'))
                END,
                NULLIF(TRIM(s.notes), '')
            FROM stg_transactions s
            LEFT JOIN utilisateurs u ON u.id_utilisateur = NULLIF(TRIM(s.cree_par_id_utilisateur), '')
            WHERE NULLIF(TRIM(s.id_transaction), '') IS NOT NULL
            ON CONFLICT (id_transaction) DO UPDATE SET
                type_transaction = EXCLUDED.type_transaction,
                reference_transaction = EXCLUDED.reference_transaction,
                cree_le = EXCLUDED.cree_le,
                cree_par_id_utilisateur = EXCLUDED.cree_par_id_utilisateur,
                statut = EXCLUDED.statut,
                notes = EXCLUDED.notes
            """
        )

    def _import_transaction_lines(self, cursor, csv_path):
        self.stdout.write("Importing lignes_transaction...")
        cols = [
            "id_transaction",
            "no_ligne",
            "id_produit",
            "quantite",
            "id_emplacement_source",
            "id_emplacement_destination",
            "lot_serie",
            "code_motif",
        ]
        self._copy_into_staging(cursor, csv_path, "stg_lignes", cols)

        cursor.execute(
            """
            INSERT INTO lignes_transaction
                (id_transaction, no_ligne, id_produit, quantite, id_emplacement_source, id_emplacement_destination, lot_serie, code_motif)
            SELECT
                t.id_transaction,
                COALESCE(NULLIF(TRIM(s.no_ligne), '')::integer, 1),
                p.id_produit,
                COALESCE(NULLIF(TRIM(s.quantite), '')::numeric, 0),
                es.id_emplacement,
                ed.id_emplacement,
                NULLIF(TRIM(s.lot_serie), ''),
                NULLIF(TRIM(s.code_motif), '')
            FROM stg_lignes s
            JOIN transactions t ON t.id_transaction = NULLIF(TRIM(s.id_transaction), '')
            LEFT JOIN produit p ON p.id_produit = NULLIF(TRIM(s.id_produit), '')
            LEFT JOIN emplacements es ON es.id_emplacement = NULLIF(TRIM(s.id_emplacement_source), '')
            LEFT JOIN emplacements ed ON ed.id_emplacement = NULLIF(TRIM(s.id_emplacement_destination), '')
            WHERE NULLIF(TRIM(s.id_transaction), '') IS NOT NULL
              AND NULLIF(TRIM(s.no_ligne), '') IS NOT NULL
            ON CONFLICT (id_transaction, no_ligne) DO UPDATE SET
                id_produit = EXCLUDED.id_produit,
                quantite = EXCLUDED.quantite,
                id_emplacement_source = EXCLUDED.id_emplacement_source,
                id_emplacement_destination = EXCLUDED.id_emplacement_destination,
                lot_serie = EXCLUDED.lot_serie,
                code_motif = EXCLUDED.code_motif
            """
        )

    def _import_demand_history(self, cursor, csv_path):
        self.stdout.write("Importing historique_demande...")
        cols = ["date", "id_produit", "quantite_demande"]
        self._copy_into_staging(cursor, csv_path, "stg_historique", cols)

        cursor.execute(
            """
            INSERT INTO historique_demande
                (date, id_produit_id, quantite_demande)
            SELECT
                COALESCE(NULLIF(TRIM(s.date), '')::timestamp::date, NOW()::date),
                p.id_produit,
                COALESCE(NULLIF(TRIM(s.quantite_demande), '')::numeric, 0)
            FROM stg_historique s
            JOIN produit p ON p.id_produit = NULLIF(TRIM(s.id_produit), '')
            WHERE NULLIF(TRIM(s.id_produit), '') IS NOT NULL
            """
        )
