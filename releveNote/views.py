from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from api.models import Etudiant
from .models import ReleveNote
from .serializers import ReleveNoteCreateSerializer, ReleveNoteListSerializer
import logging

logger = logging.getLogger(__name__)


class CreerDemandeReleveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'etudiant':
            return Response({"erreur": "Seuls les étudiants peuvent créer une demande."}, status=403)

        try:
            etudiant = Etudiant.objects.get(user=request.user)
        except Etudiant.DoesNotExist:
            return Response({"erreur": "Profil étudiant manquant."}, status=403)

        data = request.data.copy()
        data['etudiant'] = etudiant.id

        serializer = ReleveNoteCreateSerializer(data=data)
        if serializer.is_valid():
            demande = serializer.save()
            return Response({
                "success": True,
                "message": "Demande créée !",
                "numero": demande.id_releve,
                "total_exemplaires": demande.total_exemplaires(),
                "detail": demande.detail_niveaux(),
                "statut": demande.get_statut_display(),
                "date": demande.date_demande.strftime("%d/%m/%Y %H:%M")
            }, status=201)

        return Response({"erreur": "Données invalides", "details": serializer.errors}, status=400)


# Afficher demandes de l'etudiant connecté
class MesDemandesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'etudiant':
            return Response({"erreur": "Accès réservé aux étudiants."}, status=403)

        try:
            etudiant = Etudiant.objects.get(user=request.user)
        except Etudiant.DoesNotExist:
            return Response({"erreur": "Profil étudiant manquant."}, status=403)

        demandes = ReleveNote.objects.filter(etudiant=etudiant).order_by('-date_demande')
        serializer = ReleveNoteListSerializer(demandes, many=True)
        return Response({
            "total": demandes.count(),
            "demandes": serializer.data
        })


# Special scolarité: lister toutes les demandes
class ListeDemandesScolariteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'scolarite':
            return Response({"erreur": "Réservé à la scolarité."}, status=403)

        demandes = ReleveNote.objects.select_related('etudiant__user').order_by('-date_demande')
        serializer = ReleveNoteListSerializer(demandes, many=True)
        return Response({
            "total": demandes.count(),
            "demandes": serializer.data
        })


# 4. DÉTAIL D'UNE DEMANDE
class DetailDemandeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        demande = get_object_or_404(ReleveNote, pk=pk)

        if request.user.role == 'etudiant':
            try:
                etudiant = Etudiant.objects.get(user=request.user)
                if demande.etudiant != etudiant:
                    return Response({"erreur": "Accès refusé."}, status=403)
            except Etudiant.DoesNotExist:
                return Response({"erreur": "Profil étudiant manquant."}, status=403)

        elif request.user.role != 'scolarite':
            return Response({"erreur": "Accès refusé."}, status=403)

        serializer = ReleveNoteListSerializer(demande)
        return Response(serializer.data)


# 5. MODIFIER LE STATUT -> SCOLARITÉ UNIQUEMENT
# VALIDER LA DEMANDE
class ValiderDemandeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'scolarite':
            return Response({"erreur": "Réservé à la scolarité."}, status=403)

        demande = get_object_or_404(ReleveNote, pk=pk)  # Recherche par ID (pas id_releve)

        if demande.statut in ['pret', 'retire']:
            return Response({"erreur": "Cette demande est déjà validée ou retirée."}, status=400)

        demande.statut = 'pret'
        demande.date_traitement = timezone.now()
        demande.save()

        self.envoyer_email_pret(demande)

        return Response({
            "success": True,
            "message": "Demande validée avec succès !",
            "numero": demande.id_releve,
            "statut": "Prêt à retirer",
            "email_envoye": True
        }, status=200)

    def envoyer_email_pret(self, demande):
        user = demande.etudiant.user
        nom = f"{user.nom} {user.prenoms}".strip()

        send_mail(
            subject=f"Votre relevé {demande.id_releve} est prêt !",
            message=f"""
        Bonjour {nom},

        Votre relevé de notes est prêt !

        Numéro : {demande.id_releve}
        Année : {demande.annee_universitaire}
        Niveaux : {demande.detail_niveaux()}
        Total : {demande.total_exemplaires()} exemplaire(s)

        Passez à la scolarité pour le retirer.

        Cordialement,
        La Scolarité
                    """.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL or 'scolarite@ecole.com',
            recipient_list=[user.email],
            fail_silently=False,
        )


# REJETER LA DEMANDE
class RejeterDemandeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'scolarite':
            return Response({"erreur": "Réservé à la scolarité."}, status=403)

        demande = get_object_or_404(ReleveNote, pk=pk)

        if demande.statut == 'rejete':
            return Response({"erreur": "Cette demande est déjà rejetée."}, status=400)

        motif = request.data.get('motif', 'Non précisé')

        demande.statut = 'rejete'
        demande.date_traitement = timezone.now()
        demande.save()

        user = demande.etudiant.user
        nom = f"{user.nom} {user.prenoms}".strip()

        send_mail(
            subject=f"Demande {demande.id_releve} refusée",
            message=f"""
            Bonjour {nom},

            Votre demande de relevé a été refusée.

            Numéro : {demande.id_releve}
            Motif : {motif}

            Merci de contacter la scolarité.

            Cordialement.
                        """.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({
            "success": True,
            "message": "Demande rejetée",
            "numero": demande.id_releve,
            "motif": motif
        })


class EtudiantParNumeroReleveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id_releve):
        if request.user.role != 'scolarite':
            return Response({
                "erreur": "Accès refusé. Réservé à la scolarité.",
                "votre_role": request.user.role
            }, status=status.HTTP_403_FORBIDDEN)

        demande = get_object_or_404(
            ReleveNote.objects.select_related('etudiant__user'),
            id_releve__iexact=id_releve.strip()
        )

        etudiant = demande.etudiant
        user = etudiant.user

        if demande.statut in ['pret', 'retire']:
            statut_simple = "Validé"
        elif demande.statut == 'rejete':
            statut_simple = "Rejeté"
        else:
            statut_simple = "En attente"

        return Response({
            "success": True,
            "numero_releve": demande.id_releve,
            "etat_actuel": statut_simple,

            "etudiant": {
                "immatricule": etudiant.immatricule,
                "nom_complet": f"{user.nom} {user.prenoms}".strip(),
                "email": user.email,
                "contact": etudiant.contact
            },

            "demande": {
                "annee_universitaire": demande.annee_universitaire,
                "niveaux": demande.detail_niveaux(),
                "total_exemplaires": demande.total_exemplaires(),
                "date_demande": demande.date_demande.strftime("%d/%m/%Y à %H:%M"),
                "statut_detaille": demande.get_statut_display()
            }
        }, status=status.HTTP_200_OK)