from django.urls import path
from . import views

app_name = 'certificat'

urlpatterns = [
    path(
        'creer/',
        views.CreerCertificatView.as_view(),
        name='creer'),
    path(
        'mes-demandes/',
        views.MesCertificatsView.as_view(),
        name='mes-demandes'),
    path(
        'liste/',
        views.ListeCertificatsScolariteView.as_view(),
        name='liste'),
    path(
        '<int:pk>/statut/',
        views.ChangerStatutCertificatView.as_view(),
        name='statut'),
]
