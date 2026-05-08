from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from api.auth import EncomiendaTokenView, LoginCookieView, LogoutCookieView
from envios.viewsets import EncomiendaViewSet
from envios.api_views import ClienteListView, RutaListView

router = DefaultRouter()
router.register('encomiendas', EncomiendaViewSet, basename='encomienda')

urlpatterns = [
    # Autenticación JWT
    path('auth/token/',         EncomiendaTokenView.as_view(),  name='token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(),     name='token_refresh'),
    path('auth/login/',         LoginCookieView.as_view(),      name='login_cookie'),
    path('auth/logout/',        LogoutCookieView.as_view(),     name='logout_cookie'),

    # Documentación
    path('schema/', SpectacularAPIView.as_view(),                              name='schema'),
    path('docs/',   SpectacularSwaggerView.as_view(url_name='schema'),         name='swagger'),
    path('redoc/',  SpectacularRedocView.as_view(url_name='schema'),           name='redoc'),

    # Vistas genéricas de clientes y rutas
    path('clientes/', ClienteListView.as_view(), name='cliente-list'),
    path('rutas/',    RutaListView.as_view(),    name='ruta-list'),

    # ViewSets (router genera automáticamente todas las URLs CRUD)
    path('', include(router.urls)),
]
