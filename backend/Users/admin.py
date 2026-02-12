from django.contrib import admin
from .models import Utilisateur

@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('id_utilisateur', 'nom_complet', 'role', 'email', 'actif')
    list_filter = ('role', 'actif')
    search_fields = ('id_utilisateur', 'nom_complet', 'email')
    ordering = ('id_utilisateur',)
    
    fieldsets = (
        (None, {
            'fields': ('id_utilisateur', 'nom_complet', 'role', 'email', 'actif')
        }),
    )
