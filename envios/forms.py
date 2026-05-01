from django import forms
from .models import Encomienda, HistorialEstado
from clientes.models import Cliente
from rutas.models import Ruta
from config.choices import EstadoEnvio


class EncomiendaForm(forms.ModelForm):
    class Meta:
        model = Encomienda
        fields = [
            'descripcion', 'peso_kg', 'volumen_cm3',
            'remitente', 'destinatario', 'ruta',
            'costo_envio', 'fecha_entrega_est', 'observaciones',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'volumen_cm3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'remitente': forms.Select(attrs={'class': 'form-select'}),
            'destinatario': forms.Select(attrs={'class': 'form-select'}),
            'ruta': forms.Select(attrs={'class': 'form-select'}),
            'costo_envio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_entrega_est': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'descripcion': 'Descripción del paquete',
            'peso_kg': 'Peso (kg)',
            'volumen_cm3': 'Volumen (cm³)',
            'remitente': 'Remitente',
            'destinatario': 'Destinatario',
            'ruta': 'Ruta',
            'costo_envio': 'Costo de envío (S/)',
            'fecha_entrega_est': 'Fecha estimada de entrega',
            'observaciones': 'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['remitente'].queryset = Cliente.objects.activos()
        self.fields['destinatario'].queryset = Cliente.objects.activos()
        self.fields['ruta'].queryset = Ruta.objects.activas()

    def clean(self):
        cleaned = super().clean()
        remitente = cleaned.get('remitente')
        destinatario = cleaned.get('destinatario')
        if remitente and destinatario and remitente == destinatario:
            raise forms.ValidationError(
                'El remitente y el destinatario no pueden ser la misma persona.'
            )
        return cleaned


class CambioEstadoForm(forms.ModelForm):
    class Meta:
        model = HistorialEstado
        fields = ['estado_nuevo', 'observacion']
        widgets = {
            'estado_nuevo': forms.Select(attrs={'class': 'form-select'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'estado_nuevo': 'Nuevo estado',
            'observacion': 'Observación',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estado_nuevo'].choices = EstadoEnvio.choices