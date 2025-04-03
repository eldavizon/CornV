from django.db import models
from django.contrib.auth.models import User
import os

# Create your models here.

class Profile(models.Model):
    
    staff = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    address = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=20, null=True)
    image = models.ImageField(default='default.jpg', upload_to='profile_images')
    
    def __str__(self):
        return f'{self.user.username} Profile'
    
    def save(self, *args, **kwargs):
        # Antes de salvar, apaga a imagem antiga se for diferente
        try:
            old = Profile.objects.get(pk=self.pk)
            if old.image != self.image and old.image.name != 'default.jpg':
                old.image.delete(save=False)
        except Profile.DoesNotExist:
            pass
            
        super().save(*args, **kwargs)    
    
