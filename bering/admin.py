from django.contrib import admin
from gass.bering.models import *

class StationAdmin(admin.ModelAdmin):
    list_display = ('site', 'operational', 'upload_path')
    list_editable = ('operational',)
    list_filter = ('operational',)
    ordering = ('site',)
    save_on_top = True


class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ('site', 'datetime', 'notes')
    list_filter = ('ablato_adjusted',)
    ordering = ('-datetime',)


class CampaignAdmin(admin.ModelAdmin):
    list_display = ('site', 'region', 'deployment', 'recovery')
    list_editable = ('region', 'deployment', 'recovery')
    list_filter = ('site',)
    date_hierarchy = ('deployment')
    ordering = ('-deployment',)
    

admin.site.register(Station, StationAdmin)
admin.site.register(SiteVisit, SiteVisitAdmin)
admin.site.register(Campaign, CampaignAdmin)
