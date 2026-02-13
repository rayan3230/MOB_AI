import csv
from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.utils.dateparse import parse_date, parse_datetime

from Produit.models import (
    CodeBarresProduit,
    DelaisApprovisionnement,
    HistoriqueDemande,
    PolitiqueReapprovisionnement,
    Produit,
    cmd_achat_ouvertes_opt,
)
from Transaction.models import LigneTransaction, Transaction
from Users.models import Utilisateur
from warhouse.models import Emplacement, Entrepot


META_TOKENS = {"texte", "entier", "nombre", "booleen", "date", "datetime", "o", "n"}

ROLE_MAP = {
    "admin": "ADMIN",
    "administrator": "ADMIN",
    "supervisor": "SUPERVISOR",
    "responsable magasin": "SUPERVISOR",
    "operator": "EMPLOYEE",
    "employee": "EMPLOYEE",
    "preparateur de commade": "EMPLOYEE",
    "preparateur de commande": "EMPLOYEE",
    "controleur": "EMPLOYEE",
    "reciptioniste": "EMPLOYEE",
    "receptioniste": "EMPLOYEE",
}

TRANSACTION_TYPE_MAP = {
    "RECEIPT": "RECEIPT",
    "TRANSFER": "TRANSFER",
    "ISSUE": "ISSUE",
    "ADJUSTMENT": "ADJUSTMENT",
    "DELIVERY": "ISSUE",
}

DEFAULT_PASSWORD = "ChangeMe123!"


class Command(BaseCommand):
    help = "Import CSV data from folder_data/csv_export into database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv-dir",
            default="folder_data/csv_export",
            help="Directory containing exported CSV files",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Delete existing imported data before import",
        )

    def handle(self, *args, **options):
        csv_dir = Path(options["csv_dir"])
        if not csv_dir.is_absolute():
            csv_dir = Path.cwd() / csv_dir
        if not csv_dir.exists():
            self.stderr.write(self.style.ERROR(f"CSV directory not found: {csv_dir}"))
            return

        if options["truncate"]:
            self._truncate_data()

        summary = {}
        summary["utilisateurs"] = self._import_utilisateurs(csv_dir / "utilisateurs.csv")
        summary["entrepots"] = self._import_entrepots(csv_dir / "entrepots.csv")
        summary["emplacements"] = self._import_emplacements(csv_dir / "emplacements.csv")
        summary["produits"] = self._import_produits(csv_dir / "produits.csv")
        summary["codes_barres_produits"] = self._import_codes_barres(csv_dir / "codes_barres_produits.csv")
        summary["transactions"] = self._import_transactions(csv_dir / "transactions.csv")
        summary["lignes_transaction"] = self._import_lignes_transaction(csv_dir / "lignes_transaction.csv")
        summary["historique_demande"] = self._import_historique(csv_dir / "historique_demande.csv")
        summary["delais_approvisionnement"] = self._import_delais(csv_dir / "delais_approvisionnement.csv")
        summary["politique_reapprovisionnement"] = self._import_politique(csv_dir / "politique_reapprovisionnement.csv")
        summary["cmd_achat_ouvertes_opt"] = self._import_commandes_achat(csv_dir / "cmd_achat_ouvertes_opt.csv")

        self.stdout.write(self.style.SUCCESS("Import finished."))
        for name, count in summary.items():
            self.stdout.write(f"- {name}: {count}")

    def _truncate_data(self):
        with transaction.atomic():
            LigneTransaction.objects.all().delete()
            Transaction.objects.all().delete()
            cmd_achat_ouvertes_opt.objects.all().delete()
            PolitiqueReapprovisionnement.objects.all().delete()
            DelaisApprovisionnement.objects.all().delete()
            HistoriqueDemande.objects.all().delete()
            CodeBarresProduit.objects.all().delete()
            Emplacement.objects.all().delete()
            Entrepot.objects.all().delete()
            Produit.objects.all().delete()
            Utilisateur.objects.all().delete()

    def _read_rows(self, path: Path):
        if not path.exists():
            return
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for raw in reader:
                row = {self._clean(k): self._clean(v) for k, v in raw.items()}
                if self._is_empty_row(row):
                    continue
                if self._is_meta_row(row):
                    continue
                yield row

    @staticmethod
    def _clean(value):
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _is_empty_row(row):
        return all(v == "" for v in row.values())

    @staticmethod
    def _is_meta_row(row):
        non_empty = [v.lower() for v in row.values() if v != ""]
        return bool(non_empty) and all(v in META_TOKENS for v in non_empty)

    @staticmethod
    def _as_bool(value, default=False):
        if value == "":
            return default
        return value.strip().lower() in {"1", "true", "t", "yes", "y", "oui"}

    @staticmethod
    def _as_date(value):
        if not value:
            return None
        dt = parse_datetime(value)
        if dt:
            return dt.date()
        return parse_date(value)

    @staticmethod
    def _as_datetime(value):
        if not value:
            return None
        dt = parse_datetime(value)
        if dt:
            return dt
        d = parse_date(value)
        if d:
            return parse_datetime(f"{d.isoformat()} 00:00:00")
        return None

    @staticmethod
    def _as_int(value):
        if not value:
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_decimal_text(value, default="0"):
        return value if value not in {"", None} else default

    def _import_utilisateurs(self, path: Path):
        count = 0
        for row in self._read_rows(path):
            uid = row.get("id_utilisateur", "")
            name = row.get("nom_complet", "")
            if not uid or not name:
                continue

            role_raw = row.get("role", "").lower()
            role = ROLE_MAP.get(role_raw, "EMPLOYEE")

            user, created = Utilisateur.objects.get_or_create(
                id_utilisateur=uid,
                defaults={
                    "password": make_password(DEFAULT_PASSWORD),
                    "nom_complet": name,
                    "role": role,
                    "email": row.get("email") or None,
                    "actif": self._as_bool(row.get("actif", ""), True),
                },
            )

            if created:
                user.set_password(DEFAULT_PASSWORD)
            else:
                user.nom_complet = name
                user.role = role
                user.email = row.get("email") or None
                user.actif = self._as_bool(row.get("actif", ""), True)
            user.save()
            count += 1
        return count

    def _import_entrepots(self, path: Path):
        count = 0
        for row in self._read_rows(path):
            warehouse_id = row.get("id_entrepot", "")
            code = row.get("code_entrepot", "")
            name = row.get("nom_entrepot", "")
            if not warehouse_id or not code or not name:
                continue

            Entrepot.objects.update_or_create(
                id_entrepot=warehouse_id,
                defaults={
                    "code_entrepot": code,
                    "nom_entrepot": name,
                    "ville": row.get("ville") or None,
                    "adresse": row.get("adresse") or None,
                    "actif": self._as_bool(row.get("actif", ""), True),
                },
            )
            count += 1
        return count

    def _import_emplacements(self, path: Path):
        count = 0
        for row in self._read_rows(path):
            location_id = row.get("id_emplacement", "")
            code = row.get("code_emplacement", "")
            warehouse_id = row.get("id_entrepot", "")
            location_type = (row.get("type_emplacement") or "PICKING").upper()
            if location_type not in {"PICKING", "STORAGE"}:
                location_type = "PICKING"
            if not location_id or not code or not warehouse_id:
                continue

            warehouse = Entrepot.objects.filter(id_entrepot=warehouse_id).first()
            if not warehouse:
                continue

            Emplacement.objects.update_or_create(
                id_emplacement=location_id,
                defaults={
                    "code_emplacement": code,
                    "id_entrepot": warehouse,
                    "zone": row.get("zone") or None,
                    "type_emplacement": location_type,
                    "actif": self._as_bool(row.get("actif", ""), True),
                },
            )
            count += 1
        return count

    def _import_produits(self, path: Path):
        count = 0
        for row in self._read_rows(path):
            product_id = row.get("id_produit", "")
            sku = row.get("sku", "")
            name = row.get("nom_produit", "")
            if not product_id or not sku or not name:
                continue

            Produit.objects.update_or_create(
                id_produit=product_id,
                defaults={
                    "sku": sku,
                    "nom_produit": name,
                    "unite_mesure": row.get("unite_mesure") or "Unité(s)",
                    "categorie": row.get("categorie") or "N/A",
                    "actif": self._as_bool(row.get("actif", ""), True),
                },
            )
            count += 1
        return count

    def _import_codes_barres(self, path: Path):
        count = 0
        for row in self._read_rows(path):
            code = row.get("code_barres", "")
            product_id = row.get("id_produit", "")
            barcode_type = row.get("type_code_barres", "")
            if not code or not product_id or not barcode_type:
                continue

            product = Produit.objects.filter(id_produit=product_id).first()
            if not product:
                continue

            CodeBarresProduit.objects.update_or_create(
                code_barres=code,
                defaults={
                    "id_produit": product,
                    "type_code_barres": barcode_type,
                    "principal": self._as_bool(row.get("principal", ""), False),
                },
            )
            count += 1
        return count

    def _import_transactions(self, path: Path):
        count = 0
        for row in self._read_rows(path):
            transaction_id = row.get("id_transaction", "")
            tx_type_raw = (row.get("type_transaction") or "").upper()
            tx_type = TRANSACTION_TYPE_MAP.get(tx_type_raw)
            created_at = self._as_datetime(row.get("cree_le", ""))
            status = (row.get("statut") or "").upper()
            if not transaction_id or not tx_type or not created_at or not status:
                continue
            if status not in {"PENDING", "CONFIRMED", "COMPLETED", "CANCELLED"}:
                continue

            created_by_id = row.get("cree_par_id_utilisateur", "")
            created_by = Utilisateur.objects.filter(id_utilisateur=created_by_id).first() if created_by_id else None

            Transaction.objects.update_or_create(
                id_transaction=transaction_id,
                defaults={
                    "type_transaction": tx_type,
                    "reference_transaction": row.get("reference_transaction") or transaction_id,
                    "cree_le": created_at,
                    "cree_par_id_utilisateur": created_by,
                    "statut": status,
                    "notes": row.get("notes") or None,
                },
            )
            count += 1
        return count

    def _import_lignes_transaction(self, path: Path):
        count = 0
        lines_cache = []
        per_transaction_counter = defaultdict(int)
        batch_size = 3000

        for row in self._read_rows(path):
            transaction_id = row.get("id_transaction", "")
            if not transaction_id:
                continue

            transaction_obj = Transaction.objects.filter(id_transaction=transaction_id).first()
            if not transaction_obj:
                continue

            line_no = self._as_int(row.get("no_ligne", ""))
            if line_no is None:
                per_transaction_counter[transaction_id] += 1
                line_no = per_transaction_counter[transaction_id]
            else:
                per_transaction_counter[transaction_id] = max(per_transaction_counter[transaction_id], line_no)

            quantity = self._as_decimal_text(row.get("quantite", ""), "0")

            product_id = row.get("id_produit", "")
            product = Produit.objects.filter(id_produit=product_id).first() if product_id else None

            src_id = row.get("id_emplacement_source", "")
            src = Emplacement.objects.filter(id_emplacement=src_id).first() if src_id else None

            dst_id = row.get("id_emplacement_destination", "")
            dst = Emplacement.objects.filter(id_emplacement=dst_id).first() if dst_id else None

            lines_cache.append(
                LigneTransaction(
                    id_transaction=transaction_obj,
                    no_ligne=line_no,
                    id_produit=product,
                    quantite=quantity,
                    id_emplacement_source=src,
                    id_emplacement_destination=dst,
                    lot_serie=row.get("lot_serie") or None,
                    code_motif=row.get("code_motif") or None,
                )
            )

            if len(lines_cache) >= batch_size:
                LigneTransaction.objects.bulk_create(lines_cache, batch_size=batch_size, ignore_conflicts=True)
                count += len(lines_cache)
                lines_cache = []

        if lines_cache:
            LigneTransaction.objects.bulk_create(lines_cache, batch_size=batch_size, ignore_conflicts=True)
            count += len(lines_cache)

        return count

    def _import_historique(self, path: Path):
        count = 0
        history_cache = []
        batch_size = 3000

        for row in self._read_rows(path):
            history_date = self._as_date(row.get("date", ""))
            product_id = row.get("id_produit", "")
            quantity = row.get("quantite_demande", "")
            if not history_date or not product_id or quantity in {"", None}:
                continue

            product = Produit.objects.filter(id_produit=product_id).first()
            if not product:
                continue

            history_cache.append(
                HistoriqueDemande(
                    date=history_date,
                    id_produit=product,
                    quantite_demande=quantity,
                )
            )

            if len(history_cache) >= batch_size:
                HistoriqueDemande.objects.bulk_create(history_cache, batch_size=batch_size)
                count += len(history_cache)
                history_cache = []

        if history_cache:
            HistoriqueDemande.objects.bulk_create(history_cache, batch_size=batch_size)
            count += len(history_cache)

        return count

    def _import_delais(self, path: Path):
        count = 0
        for row in self._read_rows(path):
            product_id = row.get("id_produit", "")
            delay = self._as_int(row.get("delai_jours", ""))
            if not product_id or delay is None:
                continue

            product = Produit.objects.filter(id_produit=product_id).first()
            if not product:
                continue

            DelaisApprovisionnement.objects.update_or_create(
                id_produit=product,
                defaults={"delai_jours": delay},
            )
            count += 1
        return count

    def _import_politique(self, path: Path):
        count = 0
        for row in self._read_rows(path):
            product_id = row.get("id_produit", "")
            if not product_id:
                continue

            product = Produit.objects.filter(id_produit=product_id).first()
            if not product:
                continue

            PolitiqueReapprovisionnement.objects.update_or_create(
                id_produit=product,
                defaults={
                    "stock_securite": row.get("stock_securite") or None,
                    "quantite_min_commande": row.get("quantite_min_commande") or None,
                    "taille_lot": row.get("taille_lot") or None,
                },
            )
            count += 1
        return count

    def _import_commandes_achat(self, path: Path):
        count = 0
        for row in self._read_rows(path):
            purchase_order_id = row.get("id_commande_achat", "")
            product_id = row.get("id_produit", "")
            quantity = row.get("quantite_commandee", "")
            expected_date = self._as_date(row.get("date_reception_prevue", ""))
            status = (row.get("statut") or "").upper()
            if not purchase_order_id or not product_id or not quantity or not expected_date or not status:
                continue
            if status not in {"OPEN", "PARTIALLY_RECEIVED", "COMPLETED", "CANCELLED"}:
                continue

            product = Produit.objects.filter(id_produit=product_id).first()
            if not product:
                continue

            cmd_achat_ouvertes_opt.objects.update_or_create(
                id_commande_achat=purchase_order_id,
                defaults={
                    "id_produit": product,
                    "quantite_commandee": quantity,
                    "date_reception_prevue": expected_date,
                    "statut": status,
                },
            )
            count += 1
        return count
