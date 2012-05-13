from django.contrib import admin
from gass.public.models import News

class NewsAdmin(admin.ModelAdmin):
    list_display = ('headline', 'timestamp')
    search_fields = ()
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    save_on_top = True

admin.site.register(News, NewsAdmin)
