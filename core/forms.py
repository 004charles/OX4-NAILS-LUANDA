from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'email', 'phone')
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Nome Completo'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Telefone'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email já está registado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email # Use email as username
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Nome de Utilizador'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Senha'}))

from .models import Appointment, Service, Professional, User

class ReceptionistAppointmentForm(forms.ModelForm):
    # Field to select client - could be improved with autocomplete in future
    client = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='client'), 
        label="Cliente",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True), 
        label="Serviço",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    professional = forms.ModelChoiceField(
        queryset=Professional.objects.filter(is_active=True), 
        label="Profissional",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_time = forms.DateTimeField(
        label="Data e Hora",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    notes = forms.CharField(
        label="Notas", 
        required=False, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = Appointment
        fields = ['client', 'service', 'professional', 'date_time', 'notes']
