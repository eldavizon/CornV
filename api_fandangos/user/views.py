from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .forms import CreateUserForm, UserUpdateForm, ProfileUpdateForm
from django.contrib import messages
from django.core.files.base import ContentFile
import base64
from PIL import Image
from django.core.files.storage import default_storage


# Create your views here.

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('estatisticas-index')  # Substitua pelo nome correto da URL
    return redirect('user-login')  # Se não estiver logado, redireciona para login

def register(request):
    
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        
        if form.is_valid():
            form.save()
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'{username} , você foi cadastrado! Faça o login.')
            
            return redirect('user-login')
        
    else:
        form = CreateUserForm()

    
    context = {
        'form':form
        }
    
    return render(request, 'user/register.html', context)

def profile(request):
    return render(request, 'user/profile.html')

def profile_update(request):
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Verifica se está enviando uma nova imagem
            if 'image' in request.FILES or request.POST.get('cropped_image_data'):
                profile = profile_form.save(commit=False)
                
                # Apaga a imagem antiga se existir
                old_image = request.user.profile.image
                if old_image and old_image.name != 'default.jpg':  # Não apaga a imagem padrão
                    if default_storage.exists(old_image.name):
                        default_storage.delete(old_image.name)
                
                # Processa a nova imagem (cortada ou não)
                cropped_image_data = request.POST.get('cropped_image_data')
                if cropped_image_data:
                    format, imgstr = cropped_image_data.split(';base64,') 
                    ext = format.split('/')[-1]
                    data = ContentFile(base64.b64decode(imgstr), name=f'profile_{request.user.id}.{ext}')
                    profile.image.save(data.name, data, save=True)
                
                profile.save()
            
            user_form.save()
            return redirect('user-profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'user/profile_update.html', context)
