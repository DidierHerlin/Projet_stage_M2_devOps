from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from api.models import Etudiant
from .models import CertificatScolarite
from .serializers import (
    CertificatScolariteCreateSerializer,
    CertificatScolariteListSerializer
)


# 1. Créer une demande (étudiant)
class CreerCertificatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'etudiant':
            return Response(
                {"erreur": "Seuls les étudiants peuvent créer une demande de certificat."},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            etudiant = Etudiant.objects.get(user=request.user)
        except Etudiant.DoesNotExist:
            return Response(
                {"erreur": "Profil étudiant non trouvé. Veuillez contacter l'administration."},
                status=status.HTTP_404_NOT_FOUND
            )
        data = request.data.copy()
        data['etudiant'] = etudiant.id
        if 'date_naissance' not in data:
            data['date_naissance'] = None
        if 'lieu_naissance' not in data:
            data['lieu_naissance'] = ""
        serializer = CertificatScolariteCreateSerializer(data=data)
        if serializer.is_valid():
            certificat = serializer.save()
            self.envoyer_email_confirmation(certificat)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def envoyer_email_confirmation(self, certificat):
        user = certificat.etudiant.user
        nom_complet = f"{user.nom} {user.prenoms}".strip()

        sujet = f"Confirmation de demande de certificat - {
            certificat.id_certificat}"
        message = f"""
        Bonjour {nom_complet},

        Votre demande de certificat de scolarité a bien été enregistrée.

        Détails de votre demande :
        - Numéro : {certificat.id_certificat}
        - Date de la demande : {certificat.date_demande.strftime('%d/%m/%Y à %H:%M')}
        - Statut : {certificat.get_statut_display()}
        - Quantité : {certificat.quantite} exemplaire(s)

        Vous serez notifié par email à chaque changement de statut.

        Cordialement,
        Le service de la scolarité
        """

        try:
            send_mail(
                subject=sujet,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL or 'scolarite@ecole.com',
                recipient_list=[
                    user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email de confirmation : {e}")


# 2. Mes certificats (étudiant)
class MesCertificatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'etudiant':
            return Response(
                {"erreur": "Accès réservé aux étudiants."},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            etudiant = Etudiant.objects.get(user=request.user)
        except Etudiant.DoesNotExist:
            return Response(
                {"erreur": "Profil étudiant non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        certificats = CertificatScolarite.objects.filter(
            etudiant=etudiant).select_related(
            'etudiant', 'etudiant__user').order_by('-date_demande')
        serializer = CertificatScolariteListSerializer(certificats, many=True)
        stats = {
            'total': certificats.count(),
            'en_attente': certificats.filter(statut='en_attente').count(),
            'en_cours': certificats.filter(statut='en_cours').count(),
            'pret': certificats.filter(statut='pret').count(),
        }

        return Response({
            "statistiques": stats,
            "certificats": serializer.data
        }, status=status.HTTP_200_OK)

# 3. Liste pour scolarité


class ListeCertificatsScolariteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'scolarite':
            return Response(
                {"erreur": "Accès réservé au personnel de la scolarité."},
                status=status.HTTP_403_FORBIDDEN
            )
        statut = request.query_params.get('statut')
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        queryset = CertificatScolarite.objects.select_related(
            'etudiant', 'etudiant__user'
        ).order_by('-date_demande')

        if statut and statut in dict(CertificatScolarite.STATUT_CHOICES):
            queryset = queryset.filter(statut=statut)

        if date_debut:
            try:
                date_obj = timezone.datetime.strptime(
                    date_debut, '%Y-%m-%d').date()
                queryset = queryset.filter(date_demande__date__gte=date_obj)
            except ValueError:
                pass

        if date_fin:
            try:
                date_obj = timezone.datetime.strptime(
                    date_fin, '%Y-%m-%d').date()
                queryset = queryset.filter(date_demande__date__lte=date_obj)
            except ValueError:
                pass
        serializer = CertificatScolariteListSerializer(queryset, many=True)
        total = queryset.count()
        stats = {
            'total': total,
            'en_attente': queryset.filter(statut='en_attente').count(),
            'en_cours': queryset.filter(statut='en_cours').count(),
            'pret': queryset.filter(statut='pret').count(),
        }

        return Response({
            "statistiques": stats,
            "nombre_resultats": total,
            "certificats": serializer.data
        }, status=status.HTTP_200_OK)


# 4. Changer le statut + email automatique
class ChangerStatutCertificatView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if request.user.role != 'scolarite':
            return Response(
                {"erreur": "Accès réservé au personnel de la scolarité."},
                status=status.HTTP_403_FORBIDDEN
            )
        certificat = get_object_or_404(
            CertificatScolarite.objects.select_related(
                'etudiant', 'etudiant__user'), pk=pk)
        nouveau_statut = request.data.get('statut')
        if not nouveau_statut:
            return Response(
                {"erreur": "Le champ 'statut' est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST
            )
        statuts_valides = [choice[0]
                           for choice in CertificatScolarite.STATUT_CHOICES]
        if nouveau_statut not in statuts_valides:
            return Response({
                "erreur": f"Statut invalide. Statuts autorisés: {', '.join(statuts_valides)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        ancien_statut = certificat.get_statut_display()
        certificat.statut = nouveau_statut
        if nouveau_statut in ['pret', 'retire',
                              'rejete'] and not certificat.date_traitement:
            certificat.date_traitement = timezone.now()

        certificat.save()
        email_envoye = self.envoyer_email_notification(
            certificat, ancien_statut)
        response_data = {
            "success": True,
            "message": "Statut mis à jour avec succès",
            "certificat": {
                "id": certificat.id,
                "numero": certificat.id_certificat,
                "ancien_statut": ancien_statut,
                "nouveau_statut": certificat.get_statut_display(),
                "date_traitement": certificat.date_traitement.strftime("%d/%m/%Y %H:%M") if certificat.date_traitement else None
            },
            "etudiant": {
                "nom_complet": certificat.etudiant.user.get_full_name(),
                "email": certificat.etudiant.user.email,
                "immatricule": certificat.etudiant.immatricule
            },
            "email_envoye": email_envoye
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def envoyer_email_notification(self, certificat, ancien_statut):
        """Envoi un email de notification lors du changement de statut"""
        user = certificat.etudiant.user
        nom_complet = f"{user.nom} {user.prenoms}".strip()
        messages = {
            'en_cours': {
                "sujet": f"Votre certificat {certificat.id_certificat} est en traitement",
                "contenu": f"""
                    Bonjour {nom_complet},

                    Votre demande de certificat de scolarité est maintenant en cours de traitement.

                    Détails :
                    - Numéro : {certificat.id_certificat}
                    - Ancien statut : {ancien_statut}
                    - Nouveau statut : {certificat.get_statut_display()}
                    - Date de la demande : {certificat.date_demande.strftime('%d/%m/%Y')}

                    Nous vous tiendrons informé de l'avancement.

                    Cordialement,
                    Le service de la scolarité
                    """
            },
            'pret': {
                "sujet": f"Votre certificat {certificat.id_certificat} est prêt !",
                "contenu": f"""
                    Bonjour {nom_complet},

                    Votre certificat de scolarité est maintenant prêt à être retiré !

                    Détails :
                    - Numéro : {certificat.id_certificat}
                    - Quantité : {certificat.quantite} exemplaire(s)
                    - Date de traitement : {certificat.date_traitement.strftime('%d/%m/%Y à %H:%M')}

                    Vous pouvez venir le retirer au bureau de la scolarité aux horaires d'ouverture.

                    Pièces à fournir :
                    - Carte d'étudiant ou pièce d'identité

                    Cordialement,
                    Le service de la scolarité
                    """
            },
            'en_attente': {
                "sujet": f"Mise à jour de votre demande {certificat.id_certificat}",
                "contenu": f"""
                    Bonjour {nom_complet},

                    Le statut de votre demande de certificat a été modifié.

                    Détails :
                    - Numéro : {certificat.id_certificat}
                    - Ancien statut : {ancien_statut}
                    - Nouveau statut : {certificat.get_statut_display()}

                    Nous vous recontacterons lorsque votre demande sera traitée.

                    Cordialement,
                    Le service de la scolarité
                    """
            }
        }

        # Message par défaut
        message_info = messages.get(certificat.statut, {
            "sujet": f"Mise à jour de votre demande {certificat.id_certificat}",
            "contenu": f"""
            Bonjour {nom_complet},

            Le statut de votre demande de certificat a été modifié.

            Détails :
            - Numéro : {certificat.id_certificat}
            - Ancien statut : {ancien_statut}
            - Nouveau statut : {certificat.get_statut_display()}
            - Date de traitement : {certificat.date_traitement.strftime('%d/%m/%Y à %H:%M') if certificat.date_traitement else 'Non traitée'}

            Cordialement,
            Le service de la scolarité
            """
        })

        try:
            send_mail(
                subject=message_info["sujet"],
                message=message_info["contenu"],
                from_email=settings.DEFAULT_FROM_EMAIL or 'scolarite@ecole.com',
                recipient_list=[
                    user.email],
                fail_silently=True,
            )
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email de notification : {e}")
            return False
