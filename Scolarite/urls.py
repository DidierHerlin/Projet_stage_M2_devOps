from django.urls import path
from . import views

urlpatterns = [
    path(
        'toutes-demandes/',
        views.ToutesLesDemandesScolariteView.as_view(),
        name='toutes-demandes-scolarite'),
    path(
        'changer-statut/',
        views.ChangerStatutDemandeUnifieeView.as_view(),
        name='changer-statut-demande'),
    path(
        'statistiques/',
        views.StatistiquesScolariteView.as_view(),
        name='statistiques-scolarite'),
    path(
        'rechercher-demande/',
        views.RechercherDemandeParNumeroView.as_view(),
        name='rechercher-demande'),
]
