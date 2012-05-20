from django.contrib import admin
from gass.public.models import News

class NewsAdmin(admin.ModelAdmin):
    list_display = ('headline', 'timestamp')
    search_fields = ('headline',)
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

admin.site.register(News, NewsAdmin)
