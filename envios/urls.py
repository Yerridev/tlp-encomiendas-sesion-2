from django.urls import path
from . import views
from .views_cbv import EncomiendaListView, EncomiendaDetailView, EncomiendaCreateView

urlpatterns = [
    # Login/Logout
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    
    # FBV
    path('', views.dashboard, name='dashboard'),
    path('encomiendas/', views.encomienda_lista, name='encomienda_lista'),
    path('encomiendas/nueva/', views.encomienda_crear, name='encomienda_crear'),
    path('encomiendas/<int:pk>/', views.encomienda_detalle, name='encomienda_detalle'),
    path('encomiendas/<int:pk>/estado/', views.encomienda_cambiar_estado, name='encomienda_cambiar_estado'),
    path('api/encomiendas/<int:pk>/estado/', views.api_encomienda_estado, name='api_encomienda_estado'),

    # CBV
    path('cbv/encomiendas/', EncomiendaListView.as_view(), name='encomienda_lista_cbv'),
    path('cbv/encomiendas/<int:pk>/', EncomiendaDetailView.as_view(), name='encomienda_detalle_cbv'),
    path('cbv/encomiendas/nueva/', EncomiendaCreateView.as_view(), name='encomienda_crear_cbv'),
]