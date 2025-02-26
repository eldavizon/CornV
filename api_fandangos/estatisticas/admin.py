from django.contrib import admin
from .models import Produto, Retirada
from django.contrib.auth.models import Group

admin.site.site_header = 'Sistema de Controle de Estoque de Reagentes'

# Register your models here.

class ProductsAdmin(admin.ModelAdmin):
    list_display = ('nome','classificacao', 'quantidade')
    list_filter = ('classificacao',)
    
admin.site.register(Produto, ProductsAdmin)
#admin.site.unregister(Group)

admin.site.register(Retirada)

