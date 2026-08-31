from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'api/token/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair'),
    path(
        'api/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'),
    path('api/auth/token/', TokenObtainPairView.as_view()),
    path('api/auth/token/refresh/', TokenRefreshView.as_view()),
    path('api/auth/', include('rest_framework.urls')),
    path('api/password_reset/', include('django_rest_passwordreset.urls')),
    # Application
    path('api/', include('api.urls')),
    path('api/relevenote/', include('releveNote.urls')),
    path('api/certificat/', include('CertificatScolarite.urls')),
    path('api/attestation/', include('Attestation.urls')),
    path('api/scolarite/', include('Scolarite.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
