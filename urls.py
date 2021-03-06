from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('gass.api.urls')),
    url(r'^$',                      'gass.public.views.display_index',
        name='public_index'),
    url(r'^background/$',           'gass.public.views.display_about',
        name='public_about'),
    url(r'^access/$',               'gass.public.views.display_access',
        name='public_access'),
#   (r'^current/$',                 'gass.public.views.display_current'),
#   (r'^sidebar/$',                 'gass.public.views.display_sidebar'),
    url(r'^hardware/$',             'gass.public.views.display_instruments',
        name='public_instruments'),
    url(r'^team/$',                 'gass.public.views.display_team',
        name='public_team'),
#   (r'^plots/$',                   'gass.public.views.display_plot_ablation'),
#   (r'^plot/ablation/$',           'gass.public.views.display_plot_ablation'),
#   (r'^plot/mdds/$',               'gass.public.views.display_plot_mdds'),
#   (r'^plot/migration/$',          'gass.public.views.display_plot_migration'),
#   (r'^plot/conditions/$',         'gass.public.views.display_plot_conditions'),
    (r'^export/(?P<site>\w{3})$',   'gass.bering.views.export_all_records')
    )

if settings.DEBUG:
    urlpatterns += patterns('',
    (r'^gass/media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
    )
