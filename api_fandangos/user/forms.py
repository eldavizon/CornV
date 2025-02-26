from django import forms 
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.forms import UserCreationForm


class CreateUserForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
                        
        fields = ['username', 'email', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        self.fields['username'].label = "Nome de Usuário"
        self.fields['email'].label = "Endereço de E-mail"
        self.fields['password1'].label = "Senha"
        self.fields['password2'].label = "Confirmação de Senha"

         # Personalizando o help_text diretamente
        self.fields['username'].help_text = "Escolha um nome único para sua conta."
        self.fields['email'].help_text = "Usaremos esse e-mail para enviar informações importantes."
        self.fields['password1'].help_text = (
            "Sua senha não pode ser muito semelhante a outras informações pessoais. "
            "A senha deve conter pelo menos 8 caracteres. Não pode ser uma senha comumente usada, "
            "nem pode ser totalmente numérica."
        )
        self.fields['password2'].help_text = "Digite a mesma senha para confirmação."

        
        
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        
        fields = ['username', 'email', ]
        
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['address', 'phone', 'image']