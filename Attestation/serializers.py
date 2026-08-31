# attestation/serializers.py
from rest_framework import serializers
from .models import Attestation
from api.models import Etudiant
import re


class AttestationCreateSerializer(serializers.ModelSerializer):
    etudiant = serializers.PrimaryKeyRelatedField(
        queryset=Etudiant.objects.all(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Attestation
        fields = [
            'id', 'id_attestation', 'etudiant', 'type_attestation',
            'annee_scolaire', 'quantite', 'prix', 'total_paye',
            'statut', 'date_demande'
        ]
        read_only_fields = [
            'id',
            'id_attestation',
            'total_paye',
            'statut',
            'date_demande',
            'prix']

    def validate_type_attestation(self, value):
        types_valides = dict(Attestation.TYPE_ATTESTATION_CHOICES).keys()
        if value not in types_valides:
            raise serializers.ValidationError(
                f"Type invalide. Types acceptés : {', '.join(types_valides)}"
            )
        return value

    def validate_annee_scolaire(self, value):
        if value:
            if not re.match(r'^\d{4}[-/]\d{4}$', value):
                raise serializers.ValidationError(
                    "Format invalide. Attendu : 2024-2025 ou 2024/2025"
                )
            annees = re.split(r'[-/]', value)
            annee1, annee2 = int(annees[0]), int(annees[1])

            if annee2 != annee1 + 1:
                raise serializers.ValidationError(
                    f"Années incohérentes : {annee2} devrait être {annee1 + 1}"
                )

            if annee1 < 2000 or annee1 > 2100:
                raise serializers.ValidationError(
                    f"Année hors limites : {annee1}"
                )

        return value

    def validate_quantite(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "La quantité doit être au moins 1")
        if value > 10:
            raise serializers.ValidationError(
                "Maximum 10 exemplaires par demande")
        return value

    def validate(self, data):
        type_att = data.get('type_attestation')
        annee = data.get('annee_scolaire')

        if type_att == 'langue':
            if annee:
                raise serializers.ValidationError({
                    "annee_scolaire": "L'attestation de langue française n'a pas besoin d'année scolaire."
                })
            data['annee_scolaire'] = None
        elif type_att in ['fin_l3', 'fin_m1']:
            if not annee:
                raise serializers.ValidationError({
                    "annee_scolaire": "L'année scolaire est obligatoire pour les attestations de Fin d'Études."
                })
        if 'etudiant' not in data:
            raise serializers.ValidationError({
                "etudiant": "L'étudiant est requis."
            })

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update({
            "numero_attestation": instance.id_attestation,
            "type_display": instance.get_type_attestation_display(),
            "statut_display": instance.get_statut_display(),
            "etudiant_info": {
                "nom_complet": instance.etudiant.user.get_full_name(),
                "immatricule": instance.etudiant.immatricule
            } if instance.etudiant else None,
            "date_demande_formatee": instance.date_demande.strftime("%d/%m/%Y %H:%M")
        })
        return data


class AttestationListSerializer(serializers.ModelSerializer):
    etudiant_nom = serializers.CharField(
        source='etudiant.user.get_full_name', read_only=True)
    immatricule = serializers.CharField(
        source='etudiant.immatricule', read_only=True)
    type_display = serializers.CharField(
        source='get_type_attestation_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = Attestation
        fields = [
            'id', 'id_attestation', 'etudiant_nom', 'immatricule',
            'type_attestation', 'type_display', 'annee_scolaire',
            'quantite', 'prix', 'total_paye', 'statut', 'statut_display',
            'date_demande', 'date_traitement'
        ]
