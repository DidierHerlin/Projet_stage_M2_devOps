from django.urls import path
from .views import (
    CreerAttestationView,
    MesAttestationsView,
    ListeAttestationsScolariteView,
    ChangerStatutAttestationView
)

urlpatterns = [
    # Étudiant
    path('creer/', CreerAttestationView.as_view(), name='creer_attestation'),
    path(
        'mes-attestations/',
        MesAttestationsView.as_view(),
        name='mes_attestations'),

    # Scolarité
    path(
        'liste/',
        ListeAttestationsScolariteView.as_view(),
        name='liste_attestations'),
    path(
        '<int:pk>/statut/',
        ChangerStatutAttestationView.as_view(),
        name='changer_statut'),
    path(
        'changer-statut/<int:pk>/',
        ChangerStatutAttestationView.as_view(),
        name='changer_statut_alt'),
]
