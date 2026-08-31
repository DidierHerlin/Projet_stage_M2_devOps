from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from api.models import Etudiant
from .models import Attestation
from .serializers import AttestationCreateSerializer, AttestationListSerializer


class CreerAttestationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'etudiant':
            return Response(
                {"erreur": "Seuls les étudiants peuvent faire une demande."}, status=403)

        try:
            etudiant = Etudiant.objects.get(user=request.user)
        except Etudiant.DoesNotExist:
            return Response(
                {"erreur": "Profil étudiant manquant."}, status=403)

        data = request.data.copy()
        data['etudiant'] = etudiant.id

        serializer = AttestationCreateSerializer(data=data)
        if serializer.is_valid():
            attestation = serializer.save()
            return Response({
                "success": True,
                "message": "Demande d'attestation enregistrée !",
                "numero": attestation.id_attestation,
                "type": attestation.get_type_attestation_display(),
                "total": f"{attestation.total_paye} Ariary"
            }, status=201)

        return Response(serializer.errors, status=400)


class MesAttestationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'etudiant':
            return Response(
                {"erreur": "Accès réservé aux étudiants."}, status=403)

        try:
            etudiant = Etudiant.objects.get(user=request.user)
        except Etudiant.DoesNotExist:
            return Response({"erreur": "Profil manquant."}, status=403)

        attestations = Attestation.objects.filter(
            etudiant=etudiant).order_by('-date_demande')
        serializer = AttestationListSerializer(attestations, many=True)
        return Response({
            "total": attestations.count(),
            "attestations": serializer.data
        })


class ListeAttestationsScolariteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'scolarite':
            return Response({"erreur": "Réservé à la scolarité."}, status=403)

        attestations = Attestation.objects.select_related(
            'etudiant__user').order_by('-date_demande')
        serializer = AttestationListSerializer(attestations, many=True)
        return Response(serializer.data)


class ChangerStatutAttestationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'scolarite':
            return Response({"erreur": "Réservé à la scolarité."}, status=403)

        attestation = get_object_or_404(Attestation, pk=pk)
        nouveau = request.data.get('statut')

        if nouveau not in dict(Attestation.STATUT_CHOICES):
            return Response({"erreur": "Statut invalide"}, status=400)

        ancien = attestation.get_statut_display()
        attestation.statut = nouveau
        if nouveau in ['pret', 'retire', 'rejete']:
            attestation.date_traitement = timezone.now()
        attestation.save()

        # Email automatique
        self.envoyer_email(attestation, ancien)

        return Response({
            "message": "Statut mis à jour",
            "numero": attestation.id_attestation,
            "nouveau_statut": attestation.get_statut_display()
        })

    def envoyer_email(self, attestation, ancien):
        user = attestation.etudiant.user
        nom = f"{user.nom} {user.prenoms}".strip()

        if attestation.statut == 'pret':
            sujet = f"Votre attestation {
                attestation.id_attestation} est prête !"
            message = f"Bonjour {nom},\n\nVotre attestation est prête à être retirée.\n\nType : {
                attestation.get_type_attestation_display()}\nNuméro : {
                attestation.id_attestation}\n\nPassez à la scolarité.\n\nCordialement."
        else:
            sujet = f"Demande {attestation.id_attestation} mise à jour"
            message = f"Bonjour {nom},\n\nStatut changé : {ancien} → {
                attestation.get_statut_display()}\n\nCordialement."

        send_mail(
            subject=sujet,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
