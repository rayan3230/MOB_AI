import csv
from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand


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

VALID_TX_STATUS = {"PENDING", "CONFIRMED", "COMPLETED", "CANCELLED"}
VALID_PO_STATUS = {"OPEN", "PARTIALLY_RECEIVED", "COMPLETED", "CANCELLED"}


class CsvCleaner:
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = input_dir
        self.output_dir = output_dir

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
    def _to_bool(value, default="True"):
        if value == "":
            return default
        return "True" if value.lower() in {"1", "true", "t", "yes", "y", "oui"} else "False"

    def _read_rows(self, filename: str):
        path = self.input_dir / filename
        if not path.exists():
            return
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for raw in reader:
                row = {self._clean(k): self._clean(v) for k, v in raw.items()}
                if self._is_empty_row(row) or self._is_meta_row(row):
                    continue
                yield row

    def _write_csv(self, filename: str, headers, rows):
        path = self.output_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow({h: row.get(h, "") for h in headers})

    def run(self):
        produced = {}

        users_rows, user_ids = self._clean_users()
        self._write_csv(
            "utilisateurs.csv",
            [
                "id_utilisateur",
                "password",
                "nom_complet",
                "role",
                "email",
                "telephone",
                "adresse",
                "actif",
                "is_banned",
            ],
            users_rows,
        )
        produced["utilisateurs.csv"] = len(users_rows)

        warehouse_rows, warehouse_ids = self._clean_entrepots()
        self._write_csv(
            "entrepots.csv",
            ["id_entrepot", "code_entrepot", "nom_entrepot", "ville", "adresse", "actif"],
            warehouse_rows,
        )
        produced["entrepots.csv"] = len(warehouse_rows)

        emplacement_rows, emplacement_ids = self._clean_emplacements(warehouse_ids)
        self._write_csv(
            "emplacements.csv",
            [
                "id_emplacement",
                "code_emplacement",
                "id_entrepot",
                "id_niveau",
                "zone",
                "type_emplacement",
                "statut",
                "actif",
            ],
            emplacement_rows,
        )
        produced["emplacements.csv"] = len(emplacement_rows)

        produit_rows, product_ids = self._clean_produits()
        self._write_csv(
            "produits.csv",
            ["id_produit", "sku", "nom_produit", "unite_mesure", "categorie", "actif"],
            produit_rows,
        )
        produced["produits.csv"] = len(produit_rows)

        barcode_rows = self._clean_codes_barres(product_ids)
        self._write_csv(
            "codes_barres_produits.csv",
            ["code_barres", "id_produit", "type_code_barres", "principal"],
            barcode_rows,
        )
        produced["codes_barres_produits.csv"] = len(barcode_rows)

        tx_rows, tx_ids = self._clean_transactions(user_ids)
        self._write_csv(
            "transactions.csv",
            [
                "id_transaction",
                "type_transaction",
                "reference_transaction",
                "cree_le",
                "cree_par_id_utilisateur",
                "statut",
                "notes",
            ],
            tx_rows,
        )
        produced["transactions.csv"] = len(tx_rows)

        tx_lines = self._clean_lignes_transaction(tx_ids, product_ids, emplacement_ids)
        self._write_csv(
            "lignes_transaction.csv",
            [
                "id_transaction",
                "no_ligne",
                "id_produit",
                "quantite",
                "id_emplacement_source",
                "id_emplacement_destination",
                "lot_serie",
                "code_motif",
            ],
            tx_lines,
        )
        produced["lignes_transaction.csv"] = len(tx_lines)

        historique = self._clean_historique(product_ids)
        self._write_csv("historique_demande.csv", ["date", "id_produit", "quantite_demande"], historique)
        produced["historique_demande.csv"] = len(historique)

        delays = self._clean_delais(product_ids)
        self._write_csv("delais_approvisionnement.csv", ["id_produit", "delai_jours"], delays)
        produced["delais_approvisionnement.csv"] = len(delays)

        politique = self._clean_politique(product_ids)
        self._write_csv(
            "politique_reapprovisionnement.csv",
            ["id_produit", "stock_securite", "quantite_min_commande", "taille_lot"],
            politique,
        )
        produced["politique_reapprovisionnement.csv"] = len(politique)

        purchase_orders = self._clean_commandes_achat(product_ids)
        self._write_csv(
            "cmd_achat_ouvertes_opt.csv",
            ["id_commande_achat", "id_produit", "quantite_commandee", "date_reception_prevue", "statut"],
            purchase_orders,
        )
        produced["cmd_achat_ouvertes_opt.csv"] = len(purchase_orders)

        return produced

    def _clean_users(self):
        rows = []
        ids = set()
        for row in self._read_rows("utilisateurs.csv") or []:
            uid = row.get("id_utilisateur", "")
            name = row.get("nom_complet", "")
            if not uid or not name:
                continue
            rows.append(
                {
                    "id_utilisateur": uid,
                    "password": "ChangeMe123!",
                    "nom_complet": name,
                    "role": ROLE_MAP.get((row.get("role") or "").lower(), "EMPLOYEE"),
                    "email": row.get("email", ""),
                    "telephone": "",
                    "adresse": "",
                    "actif": self._to_bool(row.get("actif", ""), "True"),
                    "is_banned": "False",
                }
            )
            ids.add(uid)
        return rows, ids

    def _clean_entrepots(self):
        rows = []
        ids = set()
        for row in self._read_rows("entrepots.csv") or []:
            warehouse_id = row.get("id_entrepot", "")
            code = row.get("code_entrepot", "")
            name = row.get("nom_entrepot", "")
            if not warehouse_id or not code or not name:
                continue
            rows.append(
                {
                    "id_entrepot": warehouse_id,
                    "code_entrepot": code,
                    "nom_entrepot": name,
                    "ville": row.get("ville", ""),
                    "adresse": row.get("adresse", ""),
                    "actif": self._to_bool(row.get("actif", ""), "True"),
                }
            )
            ids.add(warehouse_id)
        return rows, ids

    def _clean_emplacements(self, warehouse_ids):
        rows = []
        ids = set()
        for row in self._read_rows("emplacements.csv") or []:
            emplacement_id = row.get("id_emplacement", "")
            warehouse_id = row.get("id_entrepot", "")
            code = row.get("code_emplacement", "")
            if not emplacement_id or not warehouse_id or not code:
                continue
            if warehouse_id not in warehouse_ids:
                continue

            location_type = (row.get("type_emplacement") or "PICKING").upper()
            if location_type not in {"PICKING", "STORAGE"}:
                location_type = "PICKING"

            rows.append(
                {
                    "id_emplacement": emplacement_id,
                    "code_emplacement": code,
                    "id_entrepot": warehouse_id,
                    "id_niveau": "",
                    "zone": row.get("zone", ""),
                    "type_emplacement": location_type,
                    "statut": "AVAILABLE",
                    "actif": self._to_bool(row.get("actif", ""), "True"),
                }
            )
            ids.add(emplacement_id)
        return rows, ids

    def _clean_produits(self):
        rows = []
        ids = set()
        for row in self._read_rows("produits.csv") or []:
            product_id = row.get("id_produit", "")
            sku = row.get("sku", "")
            name = row.get("nom_produit", "")
            if not product_id or not sku or not name:
                continue
            rows.append(
                {
                    "id_produit": product_id,
                    "sku": sku,
                    "nom_produit": name,
                    "unite_mesure": row.get("unite_mesure") or "Unité(s)",
                    "categorie": row.get("categorie") or "N/A",
                    "actif": self._to_bool(row.get("actif", ""), "True"),
                }
            )
            ids.add(product_id)
        return rows, ids

    def _clean_codes_barres(self, product_ids):
        rows = []
        for row in self._read_rows("codes_barres_produits.csv") or []:
            product_id = row.get("id_produit", "")
            code = row.get("code_barres", "")
            barcode_type = row.get("type_code_barres", "")
            if product_id not in product_ids or not code or not barcode_type:
                continue
            rows.append(
                {
                    "code_barres": code,
                    "id_produit": product_id,
                    "type_code_barres": barcode_type,
                    "principal": self._to_bool(row.get("principal", ""), "False"),
                }
            )
        return rows

    def _clean_transactions(self, user_ids):
        rows = []
        ids = set()
        for row in self._read_rows("transactions.csv") or []:
            tx_id = row.get("id_transaction", "")
            tx_type = TRANSACTION_TYPE_MAP.get((row.get("type_transaction") or "").upper())
            status = (row.get("statut") or "").upper()
            if not tx_id or not tx_type or status not in VALID_TX_STATUS:
                continue

            created_by = row.get("cree_par_id_utilisateur", "")
            if created_by and created_by not in user_ids:
                created_by = ""

            rows.append(
                {
                    "id_transaction": tx_id,
                    "type_transaction": tx_type,
                    "reference_transaction": row.get("reference_transaction") or tx_id,
                    "cree_le": row.get("cree_le", ""),
                    "cree_par_id_utilisateur": created_by,
                    "statut": status,
                    "notes": row.get("notes", ""),
                }
            )
            ids.add(tx_id)
        return rows, ids

    def _clean_lignes_transaction(self, tx_ids, product_ids, emplacement_ids):
        rows = []
        counter = defaultdict(int)
        for row in self._read_rows("lignes_transaction.csv") or []:
            tx_id = row.get("id_transaction", "")
            if tx_id not in tx_ids:
                continue

            raw_no = row.get("no_ligne", "")
            if raw_no == "":
                counter[tx_id] += 1
                line_no = str(counter[tx_id])
            else:
                try:
                    line_no_int = int(float(raw_no))
                except ValueError:
                    counter[tx_id] += 1
                    line_no_int = counter[tx_id]
                counter[tx_id] = max(counter[tx_id], line_no_int)
                line_no = str(line_no_int)

            product_id = row.get("id_produit", "")
            if product_id not in product_ids:
                product_id = ""

            src = row.get("id_emplacement_source", "")
            if src not in emplacement_ids:
                src = ""

            dst = row.get("id_emplacement_destination", "")
            if dst not in emplacement_ids:
                dst = ""

            rows.append(
                {
                    "id_transaction": tx_id,
                    "no_ligne": line_no,
                    "id_produit": product_id,
                    "quantite": row.get("quantite") or "0",
                    "id_emplacement_source": src,
                    "id_emplacement_destination": dst,
                    "lot_serie": row.get("lot_serie", ""),
                    "code_motif": row.get("code_motif", ""),
                }
            )
        return rows

    def _clean_historique(self, product_ids):
        rows = []
        for row in self._read_rows("historique_demande.csv") or []:
            product_id = row.get("id_produit", "")
            qty = row.get("quantite_demande", "")
            date_value = row.get("date", "")
            if product_id not in product_ids or qty == "" or date_value == "":
                continue
            rows.append({"date": date_value, "id_produit": product_id, "quantite_demande": qty})
        return rows

    def _clean_delais(self, product_ids):
        rows = []
        for row in self._read_rows("delais_approvisionnement.csv") or []:
            product_id = row.get("id_produit", "")
            delay = row.get("delai_jours", "")
            if product_id not in product_ids or delay == "":
                continue
            try:
                delay = str(int(float(delay)))
            except ValueError:
                continue
            rows.append({"id_produit": product_id, "delai_jours": delay})
        return rows

    def _clean_politique(self, product_ids):
        rows = []
        for row in self._read_rows("politique_reapprovisionnement.csv") or []:
            product_id = row.get("id_produit", "")
            if product_id not in product_ids:
                continue
            rows.append(
                {
                    "id_produit": product_id,
                    "stock_securite": row.get("stock_securite", ""),
                    "quantite_min_commande": row.get("quantite_min_commande", ""),
                    "taille_lot": row.get("taille_lot", ""),
                }
            )
        return rows

    def _clean_commandes_achat(self, product_ids):
        rows = []
        for row in self._read_rows("cmd_achat_ouvertes_opt.csv") or []:
            po_id = row.get("id_commande_achat", "")
            product_id = row.get("id_produit", "")
            quantity = row.get("quantite_commandee", "")
            expected = row.get("date_reception_prevue", "")
            status = (row.get("statut") or "").upper()
            if not po_id or not quantity or not expected or status not in VALID_PO_STATUS:
                continue
            if product_id not in product_ids:
                continue
            rows.append(
                {
                    "id_commande_achat": po_id,
                    "id_produit": product_id,
                    "quantite_commandee": quantity,
                    "date_reception_prevue": expected,
                    "statut": status,
                }
            )
        return rows


class Command(BaseCommand):
    help = "Clean raw csv_export into model-structured CSV files"

    def add_arguments(self, parser):
        parser.add_argument("--input-dir", default="folder_data/csv_export")
        parser.add_argument("--output-dir", default="folder_data/csv_cleaned")

    def handle(self, *args, **options):
        input_dir = Path(options["input_dir"])
        output_dir = Path(options["output_dir"])
        if not input_dir.is_absolute():
            input_dir = Path.cwd() / input_dir
        if not output_dir.is_absolute():
            output_dir = Path.cwd() / output_dir

        cleaner = CsvCleaner(input_dir=input_dir, output_dir=output_dir)
        produced = cleaner.run()

        self.stdout.write(self.style.SUCCESS(f"Cleaned CSVs written to: {output_dir}"))
        for filename, count in produced.items():
            self.stdout.write(f"- {filename}: {count}")
