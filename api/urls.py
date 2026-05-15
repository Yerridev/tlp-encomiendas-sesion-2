from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from api.auth import EncomiendaTokenView, LoginCookieView, LogoutCookieView
from envios.viewsets import EncomiendaViewSet
from envios.viewsets_v2 import EncomiendaViewSetV2
from envios.api_views import ClienteListView, RutaListView

# ── Router v1 ─────────────────────────────────────────────────────────
router_v1 = DefaultRouter()
router_v1.register('encomiendas', EncomiendaViewSet, basename='encomienda')

# ── Router v2 ─────────────────────────────────────────────────────────
router_v2 = DefaultRouter()
router_v2.register('encomiendas', EncomiendaViewSetV2, basename='encomienda')

# ── URLs compartidas (auth, docs, genericas) ──────────────────────────
shared_urlpatterns = [
    # Autenticacion JWT
    path('auth/token/',         EncomiendaTokenView.as_view(), name='token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(),    name='token_refresh'),
    path('auth/login/',         LoginCookieView.as_view(),     name='login_cookie'),
    path('auth/logout/',        LogoutCookieView.as_view(),    name='logout_cookie'),

    # Documentacion
    path('schema/', SpectacularAPIView.as_view(),                          name='schema'),
    path('docs/',   SpectacularSwaggerView.as_view(url_name='schema'),     name='swagger'),
    path('redoc/',  SpectacularRedocView.as_view(url_name='schema'),       name='redoc'),

    # Vistas genericas de clientes y rutas
    path('clientes/', ClienteListView.as_view(),  name='cliente-list'),
    path('rutas/',    RutaListView.as_view(),      name='ruta-list'),
]

# ── urlpatterns principal ─────────────────────────────────────────────
urlpatterns = [
    # Endpoints compartidos accesibles desde /api/
    path('', include(shared_urlpatterns)),

    # v1: /api/v1/encomiendas/
    path('v1/', include((router_v1.urls, 'v1'))),

    # v2: /api/v2/encomiendas/
    path('v2/', include((router_v2.urls, 'v2'))),
]
