from django import forms
from .models import Transaccion

class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = ['monto', 'tipo']  # Asegúrate de que estos campos coincidan con tu modelo
        widgets = {
            'monto': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Monto'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }
