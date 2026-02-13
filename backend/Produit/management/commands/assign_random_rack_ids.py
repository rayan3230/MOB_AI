import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from Produit.models import Produit
from warhouse.models import Rack


class Command(BaseCommand):
    help = "Assign random existing rack IDs to products (for data simulation)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Also overwrite products that already have id_rack.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max number of products to update (0 = all eligible).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Optional random seed for reproducible assignment.",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        limit = options["limit"]
        seed = options["seed"]

        if seed is not None:
            random.seed(seed)

        rack_ids = list(Rack.objects.values_list("id_rack", flat=True))
        if not rack_ids:
            self.stdout.write(self.style.WARNING("No racks found. Nothing to assign."))
            return

        if overwrite:
            queryset = Produit.objects.all().order_by("id_produit")
        else:
            queryset = Produit.objects.filter(id_rack__isnull=True).order_by("id_produit")

        if limit and limit > 0:
            queryset = queryset[:limit]

        products = list(queryset)
        if not products:
            self.stdout.write(self.style.WARNING("No eligible products found."))
            return

        with transaction.atomic():
            for product in products:
                product.id_rack_id = random.choice(rack_ids)
            Produit.objects.bulk_update(products, ["id_rack"], batch_size=1000)

        self.stdout.write(
            self.style.SUCCESS(
                f"Assigned rack IDs to {len(products)} product(s) from {len(rack_ids)} available rack(s)."
            )
        )
