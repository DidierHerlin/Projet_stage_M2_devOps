from rest_framework import serializers
from .models import ReleveNote
from api.models import Etudiant

# 1.LISTE et DÉTAIL


class ReleveNoteListSerializer(serializers.ModelSerializer):
    etudiant_nom = serializers.CharField(
        source='etudiant.user.get_full_name',
        read_only=True
    )
    immatricule = serializers.CharField(
        source='etudiant.immatricule',
        read_only=True
    )
    detail_niveaux = serializers.SerializerMethodField()
    total_exemplaires = serializers.SerializerMethodField()
    statut_display = serializers.CharField(
        source='get_statut_display',
        read_only=True
    )

    class Meta:
        model = ReleveNote
        fields = [
            'id', 'id_releve', 'etudiant', 'etudiant_nom', 'immatricule',
            'demandes', 'detail_niveaux', 'total_exemplaires',
            'annee_universitaire', 'statut', 'statut_display',
            'date_demande', 'date_traitement'
        ]
        read_only_fields = [
            'id_releve',
            'statut',
            'date_demande',
            'date_traitement',
            'etudiant_nom',
            'immatricule',
            'detail_niveaux',
            'total_exemplaires']

    def get_detail_niveaux(self, obj):
        return obj.detail_niveaux() if hasattr(obj, 'detail_niveaux') else "-"

    def get_total_exemplaires(self, obj):
        return obj.total_exemplaires()


# 2. Serializer pour CRÉATION (étudiant connecté)
class ReleveNoteCreateSerializer(serializers.ModelSerializer):
    etudiant = serializers.PrimaryKeyRelatedField(
        queryset=Etudiant.objects.all(),
        required=False,
        write_only=True
    )

    class Meta:
        model = ReleveNote
        fields = [
            'id', 'id_releve', 'etudiant', 'demandes',
            'annee_universitaire', 'statut', 'date_demande'
        ]
        read_only_fields = ['id', 'id_releve', 'statut', 'date_demande']

    def validate_demandes(self, value):
        if not value or not isinstance(value, list):
            raise serializers.ValidationError(
                "La liste des demandes est requise.")

        if len(value) == 0:
            raise serializers.ValidationError(
                "Au moins une demande est requise.")
        niveaux_valides = ['L1', 'L2', 'L3', 'M1', 'M2']

        for idx, demande in enumerate(value):
            if not isinstance(demande, dict):
                raise serializers.ValidationError(
                    f"Demande #{idx + 1} : format invalide (attendu: objet JSON)"
                )

            if 'niveau' not in demande:
                raise serializers.ValidationError(
                    f"Demande #{idx + 1} : champ 'niveau' manquant"
                )
            if 'quantite' not in demande:
                raise serializers.ValidationError(
                    f"Demande #{idx + 1} : champ 'quantite' manquant"
                )

            niveau = str(demande['niveau']).upper()
            if niveau not in niveaux_valides:
                raise serializers.ValidationError(
                    f"Demande #{
                        idx +
                        1} : niveau '{niveau}' invalide. Niveaux acceptés: {
                        ', '.join(niveaux_valides)}")

            try:
                quantite = int(demande['quantite'])
                if quantite < 1:
                    raise serializers.ValidationError(
                        f"Demande #{idx + 1} : la quantité doit être au moins 1"
                    )
                if quantite > 10:
                    raise serializers.ValidationError(
                        f"Demande #{idx + 1} : la quantité ne peut pas dépasser 10"
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Demande #{idx + 1} : quantité invalide"
                )

        return value

    def validate_annee_universitaire(self, value):
        if not value:
            raise serializers.ValidationError(
                "Au moins une année universitaire est requise.")

        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Les années doivent être fournies sous forme de liste.")

        annees_normalisees = set()

        for idx, item in enumerate(value):
            annee_str = None

            if isinstance(item, dict):
                if len(item) > 0:
                    annee_str = str(next(iter(item.keys())))
                else:
                    continue
            elif isinstance(item, (str, int)):
                annee_str = str(item)
            else:
                raise serializers.ValidationError(
                    f"Année #{idx + 1} : format invalide (attendu: nombre ou chaîne)"
                )

            annee_str = annee_str.strip()

            if not annee_str.isdigit():
                raise serializers.ValidationError(
                    f"Année #{idx + 1} : '{annee_str}' n'est pas un nombre valide"
                )

            annee = int(annee_str)

            if annee < 2000 or annee > 2100:
                raise serializers.ValidationError(
                    f"Année #{idx + 1} : {annee} hors limites (2000-2100)"
                )

            annees_normalisees.add(annee)

        if not annees_normalisees:
            raise serializers.ValidationError(
                "Aucune année valide trouvée dans la liste fournie."
            )
        return sorted(list(annees_normalisees))

    def validate(self, attrs):
        demandes = attrs.get('demandes', [])
        annees = attrs.get('annee_universitaire', [])

        if len(demandes) == 0:
            raise serializers.ValidationError({
                'demandes': "Au moins une demande est requise"
            })

        if len(annees) == 0:
            raise serializers.ValidationError({
                'annee_universitaire': "Au moins une année est requise"
            })

        total_exemplaires = sum(d.get('quantite', 0) for d in demandes)
        if total_exemplaires > 50:
            raise serializers.ValidationError(
                f"Trop d'exemplaires demandés ({total_exemplaires}). Maximum: 50")

        return attrs

    def create(self, validated_data):
        print("Création ReleveNote avec:")
        print(f"  - Demandes: {validated_data.get('demandes')}")
        print(f"  - Années: {validated_data.get('annee_universitaire')}")

        instance = super().create(validated_data)

        print(f"  ReleveNote créé: {instance.id_releve}")
        print(f"  - Demandes sauvegardées: {instance.demandes}")
        print(f"  - Années sauvegardées: {instance.annee_universitaire}")

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update({
            "numero_demande": instance.id_releve,
            "annees_universitaires": instance.annees_formatees(),
            "annees_display": instance.annees_display(),
            "total_exemplaires": instance.total_exemplaires(),
            "niveaux_demandes": instance.detail_niveaux(),
            "statut_display": instance.get_statut_display(),
            "etudiant_info": {
                "nom_complet": instance.etudiant.user.get_full_name(),
                "immatricule": instance.etudiant.immatricule
            } if instance.etudiant else None,
            "date_demande_formatee": instance.date_demande.strftime("%d/%m/%Y %H:%M")
        })

        return data


class ReleveNoteListSerializer(serializers.ModelSerializer):
    etudiant_nom = serializers.CharField(
        source='etudiant.user.get_full_name', read_only=True)
    immatricule = serializers.CharField(
        source='etudiant.immatricule', read_only=True)
    total_exemplaires = serializers.IntegerField(read_only=True)
    detail_niveaux = serializers.CharField(read_only=True)
    annees_display = serializers.CharField(read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = ReleveNote
        fields = [
            'id', 'id_releve', 'etudiant_nom', 'immatricule',
            'demandes', 'annee_universitaire', 'annees_display',
            'total_exemplaires', 'detail_niveaux',
            'statut', 'statut_display',
            'date_demande', 'date_traitement'
        ]
