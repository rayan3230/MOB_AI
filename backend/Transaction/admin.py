from django.contrib import admin
from .models import Transaction, LigneTransaction


class LigneTransactionInline(admin.TabularInline):
    """Inline admin for line items within transaction"""
    model = LigneTransaction
    extra = 1
    fields = ['no_ligne', 'id_produit', 'quantite', 'id_emplacement_source', 'id_emplacement_destination', 'lot_serie', 'code_motif']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transaction with nested line items"""
    list_display = ['id_transaction', 'type_transaction', 'statut', 'cree_le', 'cree_par_id_utilisateur']
    list_filter = ['type_transaction', 'statut']
    search_fields = ['id_transaction', 'reference_transaction']
    inlines = [LigneTransactionInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id_transaction', 'type_transaction', 'reference_transaction', 'statut')
        }),
        ('Creator & Dates', {
            'fields': ('cree_par_id_utilisateur', 'cree_le')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )


@admin.register(LigneTransaction)
class LigneTransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transaction Line Items"""
    list_display = ['id_transaction', 'no_ligne', 'id_produit', 'quantite']
    list_filter = ['id_transaction__type_transaction']
    search_fields = ['id_transaction__id_transaction', 'id_produit__nom_produit']
    
    fieldsets = (
        ('Transaction Info', {
            'fields': ('id_transaction', 'no_ligne')
        }),
        ('Product & Quantity', {
            'fields': ('id_produit', 'quantite')
        }),
        ('Locations', {
            'fields': ('id_emplacement_source', 'id_emplacement_destination')
        }),
        ('Additional Info', {
            'fields': ('lot_serie', 'code_motif')
        }),
    )
