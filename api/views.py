# api/views.py

from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import (JSONParser, MultiPartParser, FormParser)
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.mail import send_mail
import logging

from .serializers import (
    EtudiantSerializer,
    ScolariteSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UpdateProfilePhotoSerializer,
    PasswordResetRequestSerializer,
    PasswordResetCodeVerificationSerializer,
    PasswordResetConfirmSerializer
)
from .models import Etudiant, User
from gestion_papier_scolarite.utils.token_utils import generate_reset_token, get_token_expiration

logger = logging.getLogger(__name__)


# ===================================================================
# AUTHENTIFICATION
# ===================================================================

class LoginView(APIView):
    """Connexion utilisateur"""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'success': False,
                'error': 'Email et mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)

        if user:
            auth_login(request, user)
            serializer = UserSerializer(user, context={'request': request})
            return Response({
                'success': True,
                'message': 'Connexion réussie',
                'user': serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'error': 'Email ou mot de passe incorrect'
        }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """Déconnexion utilisateur"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth_logout(request)
        return Response({
            'success': True,
            'message': 'Déconnexion réussie'
        }, status=status.HTTP_200_OK)


# ===================================================================
# INSCRIPTION
# ===================================================================

class EtudiantRegisterView(APIView):
    """Inscription des étudiants"""
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        logger.info(
            f"Tentative d'inscription étudiant: {
                request.data.get('email')}")

        serializer = EtudiantSerializer(
            data=request.data, context={
                'request': request})

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    etudiant = serializer.save()

                logger.info(
                    f"Étudiant créé avec succès: {
                        etudiant.user.email}")

                return Response({
                    'success': True,
                    'message': 'Inscription réussie',
                    'data': EtudiantSerializer(etudiant, context={'request': request}).data
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(
                    f"Erreur lors de la création de l'étudiant: {
                        str(e)}")
                return Response({
                    'success': False,
                    'error': 'Erreur lors de la création du compte',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.warning(f"Validation échouée: {serializer.errors}")

        return Response({
            'success': False,
            'error': 'Données invalides',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ScolariteRegisterView(APIView):
    """Inscription du personnel de scolarité"""
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        logger.info(
            f"Tentative d'inscription scolarité: {
                request.data.get('email')}")

        serializer = ScolariteSerializer(
            data=request.data, context={
                'request': request})

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    scolarite = serializer.save()

                logger.info(f"Compte scolarité créé: {scolarite.user.email}")

                return Response({
                    'success': True,
                    'message': 'Compte scolarité créé avec succès',
                    'data': {
                        'email': scolarite.user.email,
                        'nom_complet': f"{scolarite.user.nom} {scolarite.user.prenoms}",
                        'fonction': scolarite.fonction
                    }
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Erreur création scolarité: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'Erreur lors de la création du compte',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.warning(f"Validation scolarité échouée: {serializer.errors}")

        return Response({
            'success': False,
            'error': 'Données invalides',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ===================================================================
# GESTION PROFIL ÉTUDIANT
# ===================================================================

class EtudiantDetailView(APIView):
    """Détails et modification du profil étudiant"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        """
        GET /api/etudiant/me/     → Profil de l'utilisateur connecté
        GET /api/etudiant/<id>/   → Profil spécifique (scolarité uniquement)
        """
        if pk:
            # Accès à un profil spécifique - réservé à la scolarité
            if request.user.role != 'scolarite':
                return Response({
                    'success': False,
                    'error': 'Accès refusé. Réservé à la scolarité.'
                }, status=status.HTTP_403_FORBIDDEN)

            etudiant = get_object_or_404(Etudiant, pk=pk)
        else:
            # Accès à son propre profil
            try:
                etudiant = Etudiant.objects.get(user=request.user)
            except Etudiant.DoesNotExist:
                # Cas où c'est un membre de la scolarité
                if request.user.role == 'scolarite':
                    return Response({
                        'success': True,
                        'message': 'Vous êtes connecté en tant que scolarité',
                        'user': UserSerializer(request.user, context={'request': request}).data
                    }, status=status.HTTP_200_OK)

                return Response({
                    'success': False,
                    'error': 'Profil étudiant non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)

        serializer = EtudiantSerializer(etudiant, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk=None):
        """Mise à jour du profil (étudiant uniquement, son propre profil)"""
        # Vérifier que l'utilisateur est un étudiant
        try:
            etudiant = Etudiant.objects.get(user=request.user)
        except Etudiant.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Vous devez être un étudiant pour modifier un profil'
            }, status=status.HTTP_403_FORBIDDEN)

        # Vérifier qu'il modifie bien son propre profil
        if pk and str(etudiant.pk) != str(pk):
            return Response({
                'success': False,
                'error': 'Vous ne pouvez modifier que votre propre profil'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = EtudiantSerializer(
            etudiant,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    etudiant_updated = serializer.save()

                return Response({
                    'success': True,
                    'message': 'Profil mis à jour avec succès',
                    'data': EtudiantSerializer(etudiant_updated, context={'request': request}).data
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Erreur mise à jour étudiant: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'Erreur lors de la mise à jour',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': False,
            'error': 'Données invalides',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        """Suppression (scolarité uniquement)"""
        if request.user.role != 'scolarite':
            return Response({
                'success': False,
                'error': 'Seule la scolarité peut supprimer un étudiant'
            }, status=status.HTTP_403_FORBIDDEN)

        if not pk:
            return Response({
                'success': False,
                'error': 'ID de l\'étudiant requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        etudiant = get_object_or_404(Etudiant, pk=pk)
        user = etudiant.user

        try:
            with transaction.atomic():
                etudiant.delete()
                user.delete()

            logger.info(f"Étudiant supprimé: {user.email}")

            return Response({
                'success': True,
                'message': 'Étudiant supprimé avec succès'
            }, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Erreur suppression étudiant: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la suppression',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EtudiantListView(APIView):
    """Liste de tous les étudiants (scolarité uniquement)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'scolarite':
            return Response({
                'success': False,
                'error': 'Accès refusé. Réservé à la scolarité.'
            }, status=status.HTTP_403_FORBIDDEN)

        etudiants = Etudiant.objects.select_related('user').all()
        serializer = EtudiantSerializer(
            etudiants, many=True, context={
                'request': request})

        return Response({
            'success': True,
            'count': etudiants.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


# ===================================================================
# GESTION PROFIL UTILISATEUR
# ===================================================================

class GetProfileView(APIView):
    """Récupérer le profil de l'utilisateur connecté"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response({
            'success': True,
            'user': serializer.data
        }, status=status.HTTP_200_OK)


class UpdateUserProfileView(APIView):
    """Mise à jour complète du profil utilisateur"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                user = serializer.save()

                return Response({
                    'success': True,
                    'message': 'Profil mis à jour avec succès',
                    'user': UserSerializer(user, context={'request': request}).data
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Erreur mise à jour profil: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'Erreur lors de la mise à jour',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': False,
            'error': 'Données invalides',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UpdateProfilePhotoView(APIView):
    """Mise à jour de la photo de profil uniquement"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = UpdateProfilePhotoSerializer(data=request.data)

        if serializer.is_valid():
            try:
                user = request.user

                # Supprimer l'ancienne photo si elle existe
                if user.photo_profil:
                    user.photo_profil.delete(save=False)

                # Mettre à jour avec la nouvelle photo
                user.photo_profil = serializer.validated_data['photo_profil']
                user.save()

                return Response({
                    'success': True,
                    'message': 'Photo de profil mise à jour avec succès',
                    'user': UserSerializer(user, context={'request': request}).data
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Erreur mise à jour photo: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'Erreur lors de la mise à jour de la photo',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': False,
            'error': 'Données invalides',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DeleteProfilePhotoView(APIView):
    """Suppression de la photo de profil"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user

        if not user.photo_profil:
            return Response({
                'success': False,
                'error': 'Aucune photo de profil à supprimer'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user.photo_profil.delete(save=True)

            return Response({
                'success': True,
                'message': 'Photo de profil supprimée avec succès'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Erreur suppression photo: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur lors de la suppression de la photo',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangePasswordView(APIView):
    """Changement de mot de passe (nécessite l'ancien mot de passe)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({
                'success': False,
                'error': 'Mot de passe actuel et nouveau mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserUpdateSerializer(
            request.user,
            data={
                'current_password': current_password,
                'new_password': new_password
            },
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                serializer.save()

                logger.info(f"Mot de passe changé pour: {request.user.email}")

                return Response({
                    'success': True,
                    'message': 'Mot de passe changé avec succès'
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Erreur changement mot de passe: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'Erreur lors du changement de mot de passe',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': False,
            'error': 'Validation échouée',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ===================================================================
# RÉINITIALISATION MOT DE PASSE (3 étapes)
# ===================================================================

@method_decorator(csrf_exempt, name='dispatch')
class RequestPasswordResetView(APIView):
    """Étape 1 : Demande de réinitialisation - Envoie un code par email"""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Email invalide',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)

            # Générer le token
            token = generate_reset_token()
            expiration = get_token_expiration()

            # Sauvegarder dans la base
            user.reset_token = token
            user.reset_token_expiration = expiration
            user.save()

            # Envoyer l'email
            try:
                send_mail(
                    subject="Code de réinitialisation de mot de passe",
                    message=f"""Bonjour {user.nom} {user.prenoms},

Vous avez demandé la réinitialisation de votre mot de passe.

Votre code de vérification est : {token}

Ce code est valide pendant 10 minutes.

Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email.

Cordialement,
L'équipe de gestion""",
                    from_email=None,
                    recipient_list=[email],
                    fail_silently=False,
                )

                logger.info(f"Code de réinitialisation envoyé à: {email}")

                return Response({
                    'success': True,
                    'message': 'Code envoyé par email avec succès'
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Erreur envoi email: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'Erreur lors de l\'envoi de l\'email',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except User.DoesNotExist:
            # Pour des raisons de sécurité, on peut renvoyer un message
            # générique
            return Response({
                'success': False,
                'error': 'Aucun compte associé à cet email'
            }, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name='dispatch')
class VerifyResetCodeView(APIView):
    """Étape 2 : Vérification du code"""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetCodeVerificationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Données invalides',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(email=email)

            if not user.reset_token:
                return Response({
                    'success': False,
                    'error': 'Aucun code de réinitialisation trouvé'
                }, status=status.HTTP_400_BAD_REQUEST)

            if user.reset_token != code:
                return Response({
                    'success': False,
                    'error': 'Code incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)

            if user.reset_token_expiration < timezone.now():
                return Response({
                    'success': False,
                    'error': 'Le code a expiré. Veuillez demander un nouveau code'
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'success': True,
                'message': 'Code valide'
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Utilisateur introuvable'
            }, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name='dispatch')
class ResetPasswordView(APIView):
    """Étape 3 : Réinitialisation finale du mot de passe"""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Données invalides',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)

            if not user.reset_token or user.reset_token != code:
                return Response({
                    'success': False,
                    'error': 'Code invalide'
                }, status=status.HTTP_400_BAD_REQUEST)

            if user.reset_token_expiration < timezone.now():
                return Response({
                    'success': False,
                    'error': 'Le code a expiré'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Changer le mot de passe
            user.set_password(new_password)

            # Supprimer le token
            user.reset_token = None
            user.reset_token_expiration = None
            user.save()

            logger.info(f"Mot de passe réinitialisé pour: {email}")

            return Response({
                'success': True,
                'message': 'Mot de passe réinitialisé avec succès'
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Utilisateur introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
