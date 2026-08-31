from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Etudiant, Scolarite


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'nom', 'prenoms', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('email', 'nom', 'prenoms')
    ordering = ('email',)

    fieldsets = (
        (None, {
            'fields': (
                'email', 'password')}), ('Informations personnelles', {
                    'fields': (
                        'nom', 'prenoms', 'role')}), ('Permissions', {
                            'fields': (
                                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}), )

    add_fieldsets = (
        (None, {
            'classes': (
                'wide',), 'fields': (
                'email', 'nom', 'prenoms', 'role', 'password1', 'password2', 'is_staff', 'is_active')}), )

    filter_horizontal = ('groups', 'user_permissions',)


@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = (
        'immatricule',
        'get_nom',
        'get_prenoms',
        'get_email',
        'contact')
    list_filter = ('user__role',)
    search_fields = (
        'immatricule',
        'user__nom',
        'user__prenoms',
        'user__email',
        'contact')
    ordering = ('immatricule',)

    def get_nom(self, obj):
        return obj.user.nom
    get_nom.short_description = 'Nom'
    get_nom.admin_order_field = 'user__nom'

    def get_prenoms(self, obj):
        return obj.user.prenoms
    get_prenoms.short_description = 'Prénoms'
    get_prenoms.admin_order_field = 'user__prenoms'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'


@admin.register(Scolarite)
class ScolariteAdmin(admin.ModelAdmin):
    list_display = ('get_nom', 'get_prenoms', 'get_email', 'fonction')
    search_fields = ('user__nom', 'user__prenoms', 'user__email', 'fonction')

    def get_nom(self, obj):
        return obj.user.nom
    get_nom.short_description = 'Nom'
    get_nom.admin_order_field = 'user__nom'

    def get_prenoms(self, obj):
        return obj.user.prenoms
    get_prenoms.short_description = 'Prénoms'
    get_prenoms.admin_order_field = 'user__prenoms'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
