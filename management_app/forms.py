from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Accident, Alert, CongestionReport, Profile


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'id': 'id_username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'id_password',
        })
    )


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=40,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name (optional)'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        if 'username' in self.fields:
            self.fields['username'].widget.attrs.update({'placeholder': 'Choose unique username'})
            self.fields['username'].help_text = 'Letters, digits and @/./+/-/_ only.'
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({'placeholder': 'Create password (min 8 characters)'})
            self.fields['password1'].help_text = 'Password must be at least 8 characters long.'
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm your password'})
            self.fields['password2'].help_text = 'Re-enter the exact password for confirmation.'

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is used by another account.')
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('phone', 'city')


class AccidentForm(forms.ModelForm):
    occurred_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = Accident
        fields = ('title', 'location', 'severity', 'vehicles_involved', 'injuries',
                  'occurred_at', 'description', 'status')
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, is_staff=False, **kwargs):
        super().__init__(*args, **kwargs)
        # Only staff members may change the status of a report.
        if not is_staff:
            del self.fields['status']
        if not self.instance.pk:
            self.fields['occurred_at'].initial = timezone.localtime().strftime('%Y-%m-%dT%H:%M')
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-select' if isinstance(f.widget, forms.Select) else 'form-control')

    def clean_occurred_at(self):
        value = self.cleaned_data['occurred_at']
        if value > timezone.now():
            raise forms.ValidationError('Accident time cannot be in the future.')
        return value

    def clean_vehicles_involved(self):
        v = self.cleaned_data['vehicles_involved']
        if v < 1:
            raise forms.ValidationError('At least one vehicle must be involved.')
        return v


class CongestionForm(forms.ModelForm):
    reported_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = CongestionReport
        fields = ('location', 'level', 'average_speed', 'cause', 'reported_at', 'notes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['reported_at'].initial = timezone.localtime().strftime('%Y-%m-%dT%H:%M')
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-select' if isinstance(f.widget, forms.Select) else 'form-control')

    def clean_average_speed(self):
        v = self.cleaned_data['average_speed']
        if v > 120:
            raise forms.ValidationError('Speed above 120 km/h looks incorrect.')
        return v


class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ('title', 'message', 'location', 'priority', 'is_active')
        widgets = {'message': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            if name == 'is_active':
                f.widget.attrs['class'] = 'form-check-input'
            else:
                f.widget.attrs.setdefault('class', 'form-select' if isinstance(f.widget, forms.Select) else 'form-control')
