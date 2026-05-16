from django.urls import path,include
from .views import (
    EtudiantRegisterView, 
    ScolariteRegisterView,
    EtudiantDetailView,
    EtudiantListView,
    LoginView,
    LogoutView,
    RequestPasswordResetView, 
    VerifyResetCodeView,
    ResetPasswordView,
    GetProfileView,
    UpdateUserProfileView,
    UpdateProfilePhotoView,
    DeleteProfilePhotoView,
    ChangePasswordView
)
urlpatterns = [
    # Inscription
    path('register/etudiant/', EtudiantRegisterView.as_view(), name='register-etudiant'),
    path('register/scolarite/', ScolariteRegisterView.as_view(), name='register-scolarite'),
    
    # Liste des étudiants
    path('etudiants/', EtudiantListView.as_view(), name='etudiant-list'),

    # Profil de l'étudiant connecté
    path('etudiant/me/', EtudiantDetailView.as_view(), name='etudiant-me'),    

    # Détails étudiant (GET, PUT, DELETE)
    path('etudiant/<int:pk>/', EtudiantDetailView.as_view(), name='etudiant-detail'),
    


    path('accounts/', include(('django.contrib.auth.urls', 'accounts'))),
    path('auth/', include(('django.contrib.auth.urls', 'auth'))),

    path('auth/login/', LoginView.as_view()),
    path('auth/logout/', LogoutView.as_view()),

    #mot de passe oublié
    path("request-reset/", RequestPasswordResetView.as_view()),
    path("verify-code/", VerifyResetCodeView.as_view(), name="verify-reset-code"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),

    #modifer  mot de passe et info user
     path('profile/', GetProfileView.as_view(), name='get_profile'),
    # Mettre à jour mon profil complet
    path('profile/update/', UpdateUserProfileView.as_view(), name='update_profile'),
    # Gérer la photo de profil
    path('profile/photo/', UpdateProfilePhotoView.as_view(), name='update_photo'),
    path('profile/photo/delete/', DeleteProfilePhotoView.as_view(), name='delete_photo'),
    # Changer le mot de passe
    path('profile/password/change/', ChangePasswordView.as_view(), name='change-password'),
]
