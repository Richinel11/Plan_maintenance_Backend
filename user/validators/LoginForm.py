from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate


class LoginForm(forms.Form):
    username = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}), required=True)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('Veuillez fournir votre nom utilisateur.')
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise ValidationError('Mot de passe requis.')
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        # Check if the username and password are valid (you can customize this logic)
        user = authenticate(email=email, password=password)
        if user is None:
            raise ValidationError('Email ou mot de passe invalid')

        return cleaned_data