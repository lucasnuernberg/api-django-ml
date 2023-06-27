from django.contrib import admin
from .models import ContaML, TokenMl, RespostaPadrao, Device, Notification

admin.site.register(TokenMl)
admin.site.register(ContaML)
admin.site.register(RespostaPadrao)
admin.site.register(Device)
admin.site.register(Notification)