# releveNote/urls.py → VERSION OPTIMISÉE & PROFESSIONNELLE
from django.urls import path
from . import views

app_name = 'releveNote'

urlpatterns = [
    # ÉTUDIANT
    path('creer/', views.CreerDemandeReleveView.as_view(), name='creer'),
    path(
        'mes-demandes/',
        views.MesDemandesView.as_view(),
        name='mes-demandes'),
    path('detail/<int:pk>/', views.DetailDemandeView.as_view(), name='detail'),

    # SCOLARITÉ
    path(
        'liste/',
        views.ListeDemandesScolariteView.as_view(),
        name='liste-scolarite'),
    path(
        '<int:pk>/valider/',
        views.ValiderDemandeView.as_view(),
        name='valider-demande'),
    path(
        '<int:pk>/rejeter/',
        views.RejeterDemandeView.as_view(),
        name='rejeter-demande'),

    path(
        'etudiant-par-numero/<str:id_releve>/',
        views.EtudiantParNumeroReleveView.as_view(),
        name='etudiant-par-numero'
    ),
]
