from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm

from .models import Encomienda, Empleado, HistorialEstado
from config.choices import EstadoEnvio
from .forms import EncomiendaForm, CambioEstadoForm


def login_view(request):
    """Vista de login con formulario"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Cierra sesión y redirige al login"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


@login_required
def perfil_view(request):
    """Perfil del empleado"""
    try:
        empleado = Empleado.objects.get(email=request.user.email)
    except Empleado.DoesNotExist:
        empleado = None
    return render(request, 'accounts/perfil.html', {'empleado': empleado})


@login_required
def dashboard(request):
    """Dashboard con estadísticas del sistema"""
    try:
        hoy = timezone.now().date()
        context = {
            'pendientes': Encomienda.objects.pendientes().count(),
            'en_transito': Encomienda.objects.en_transito().count(),
            'en_destino': Encomienda.objects.filter(estado=EstadoEnvio.EN_DESTINO).count(),
            'con_retraso': Encomienda.objects.con_retraso().count(),
            'entregadas': Encomienda.objects.filter(estado=EstadoEnvio.ENTREGADO).count(),
            'entregadas_hoy': Encomienda.objects.filter(
                estado=EstadoEnvio.ENTREGADO,
                fecha_entrega_real=hoy
            ).count(),
            'ultimas': Encomienda.objects.con_relaciones()[:5],
        }
    except Exception as e:
        context = {
            'pendientes': 0,
            'en_transito': 0,
            'en_destino': 0,
            'con_retraso': 0,
            'entregadas': 0,
            'entregadas_hoy': 0,
            'ultimas': [],
            'error': str(e)
        }
    return render(request, 'envios/dashboard.html', context)


@login_required
def encomienda_lista(request):
    qs = Encomienda.objects.con_relaciones()
    estado = request.GET.get('estado', '')
    q = request.GET.get('q', '')

    if estado:
        qs = qs.filter(estado=estado)
    if q:
        qs = qs.filter(
            Q(codigo__icontains=q) |
            Q(remitente__apellidos__icontains=q) |
            Q(destinatario__apellidos__icontains=q)
        )

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page', 1)
    encomiendas = paginator.get_page(page_number)

    return render(request, 'envios/lista.html', {
        'encomiendas': encomiendas,
        'estados': EstadoEnvio.choices,
        'estado_activo': estado,
        'q': q,
    })


@login_required
def encomienda_detalle(request, pk):
    enc = get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)
    historial = enc.historial.select_related('empleado').all()
    cambio_estado_form = CambioEstadoForm(initial={"estado_nuevo": enc.estado})
    return render(request, 'envios/detalle.html', {
        'encomienda': enc,
        'historial': historial,
        'cambio_estado_form': cambio_estado_form,
    })


@login_required
def encomienda_crear(request):
    if request.method == 'POST':
        form = EncomiendaForm(request.POST)
        if form.is_valid():
            enc = form.save(commit=False)
            enc.empleado_registro = Empleado.objects.get(email=request.user.email)
            enc.save()
            messages.success(request, f'Encomienda {enc.codigo} registrada correctamente.')
            return redirect('encomienda_detalle', pk=enc.pk)
    else:
        form = EncomiendaForm()
    return render(request, 'envios/form.html', {
        'form': form,
        'titulo': 'Nueva Encomienda',
    })


@login_required
@permission_required('envios.change_encomienda', raise_exception=True)
@require_POST
def encomienda_cambiar_estado(request, pk):
    enc = get_object_or_404(Encomienda, pk=pk)
    form = CambioEstadoForm(request.POST)
    nuevo_estado = None
    observacion = ''
    try:
        empleado = Empleado.objects.get(email=request.user.email)
        if form.is_valid():
            nuevo_estado = form.cleaned_data['estado_nuevo']
            observacion = form.cleaned_data.get('observacion', '')
            enc.cambiar_estado(nuevo_estado, empleado, observacion)
            messages.success(request, 'Estado actualizado correctamente.')
            return redirect('encomienda_detalle', pk=pk)
        raise ValueError('Formulario inválido.')
    except (ValueError, Empleado.DoesNotExist) as e:
        messages.error(request, str(e))
    return redirect('encomienda_detalle', pk=pk)


@login_required
def api_encomienda_estado(request, pk):
    enc = get_object_or_404(Encomienda, pk=pk)
    return JsonResponse({
        'codigo': enc.codigo,
        'estado': enc.estado,
        'estado_display': enc.get_estado_display(),
        'tiene_retraso': enc.tiene_retraso,
        'dias_en_transito': enc.dias_en_transito,
        'esta_entregada': enc.esta_entregada,
    })
