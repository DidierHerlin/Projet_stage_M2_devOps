from rest_framework import serializers
from .models import CertificatScolarite
from api.models import Etudiant


def get_user_full_name(user):
    """Retourne le nom complet d'un utilisateur selon le modèle défini"""
    if hasattr(user, 'nom') and hasattr(user, 'prenoms'):
        return f"{user.nom} {user.prenoms}".strip()
    elif hasattr(user, 'first_name') and hasattr(user, 'last_name'):
        return f"{user.first_name} {user.last_name}".strip()
    else:
        return user.email

# 1. CRÉATION DE DEMANDE


class CertificatScolariteCreateSerializer(serializers.ModelSerializer):
    etudiant = serializers.PrimaryKeyRelatedField(
        queryset=Etudiant.objects.all(),
        required=False,
        write_only=True
    )

    date_naissance = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=['%d/%m/%Y', '%Y-%m-%d']
    )

    lieu_naissance = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=150
    )

    class Meta:
        model = CertificatScolarite
        fields = [
            'id', 'id_certificat', 'etudiant',
            'nom_pere', 'nom_mere', 'date_naissance', 'lieu_naissance',
            'quantite', 'statut', 'date_demande', 'date_traitement'
        ]
        read_only_fields = [
            'id_certificat',
            'statut',
            'date_demande',
            'date_traitement']

    def validate(self, data):
        if not data.get('nom_pere') or data.get('nom_pere') == "Non spécifié":
            raise serializers.ValidationError(
                {"nom_pere": "Le nom du père est obligatoire."}
            )
        if not data.get('nom_mere') or data.get('nom_mere') == "Non spécifiée":
            raise serializers.ValidationError(
                {"nom_mere": "Le nom de la mère est obligatoire."}
            )

        quantite = data.get('quantite', 1)
        if not (1 <= quantite <= 10):
            raise serializers.ValidationError(
                {"quantite": "La quantité doit être comprise entre 1 et 10 exemplaires."}
            )

        date_naissance = data.get('date_naissance')
        if date_naissance:
            from django.utils import timezone
            if date_naissance > timezone.now().date():
                raise serializers.ValidationError(
                    {"date_naissance": "La date de naissance ne peut pas être dans le futur."}
                )

        return data

    def to_representation(self, instance):
        return {
            "success": True,
            "message": "Demande de certificat enregistrée avec succès !",
            "numero": instance.id_certificat,
            "statut": instance.get_statut_display(),
            "date_demande": instance.date_demande.strftime("%d/%m/%Y à %H:%M"),
            "etudiant": {
                "nom_complet": get_user_full_name(
                    instance.etudiant.user),
                "immatricule": instance.etudiant.immatricule},
            "details": {
                "nom_pere": instance.nom_pere,
                "nom_mere": instance.nom_mere,
                "quantite": instance.quantite,
                "date_naissance": instance.date_naissance.strftime("%d/%m/%Y") if instance.date_naissance else None,
                "lieu_naissance": instance.lieu_naissance}}

# 2. LISTE et DÉTAIL


class CertificatScolariteListSerializer(serializers.ModelSerializer):
    etudiant_nom = serializers.SerializerMethodField()
    immatricule = serializers.CharField(
        source='etudiant.immatricule', read_only=True)
    email = serializers.CharField(source='etudiant.user.email', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    peut_etre_retire = serializers.SerializerMethodField()
    date_naissance_formatted = serializers.SerializerMethodField()
    date_demande_formatted = serializers.SerializerMethodField()
    date_traitement_formatted = serializers.SerializerMethodField()
    lieu_naissance = serializers.CharField(read_only=True)  # Ajouté

    class Meta:
        model = CertificatScolarite
        fields = [
            'id',
            'id_certificat',
            'etudiant_nom',
            'immatricule',
            'email',
            'nom_pere',
            'nom_mere',
            'date_naissance',
            'date_naissance_formatted',
            'lieu_naissance',
            'quantite',
            'statut',
            'statut_display',
            'date_demande',
            'date_demande_formatted',
            'date_traitement',
            'date_traitement_formatted',
            'peut_etre_retire']

    def get_etudiant_nom(self, obj):
        return get_user_full_name(obj.etudiant.user)

    def get_peut_etre_retire(self, obj):
        return obj.statut == 'pret'

    def get_date_naissance_formatted(self, obj):
        if obj.date_naissance:
            return obj.date_naissance.strftime("%d/%m/%Y")
        return None

    def get_date_demande_formatted(self, obj):
        if obj.date_demande:
            return obj.date_demande.strftime("%d/%m/%Y %H:%M")
        return None

    def get_date_traitement_formatted(self, obj):
        if obj.date_traitement:
            return obj.date_traitement.strftime("%d/%m/%Y %H:%M")
        return None

# 3. CHANGEMENT DE STATUT


class ChangerStatutCertificatSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificatScolarite
        fields = ['statut']
        read_only_fields = ['id_certificat']
