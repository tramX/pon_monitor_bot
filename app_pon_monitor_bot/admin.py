from django.contrib import admin

from app_pon_monitor_bot import models

admin.site.register(models.Client)
admin.site.register(models.BDCOM)
admin.site.register(models.MikroTik)
admin.site.register(models.Message)
admin.site.register(models.Organization)
