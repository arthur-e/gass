from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^$',                         'gass.public.views.display_index'),
#   (r'^test/$',                    'gass.public.views.display_current'),
#   (r'^about/$',                   'gass.public.views.display_about'),
#   (r'^access/$',                  'gass.public.views.display_data_access'),
#   (r'^current/$',                 'gass.public.views.display_current'),
#   (r'^sidebar/$',                 'gass.public.views.display_sidebar'),
#   (r'^instrumentation/$',         'gass.public.views.display_instrumentation'),
#   (r'^team/$',                    'gass.public.views.display_team'),
#   (r'^plots/$',                   'gass.public.views.display_plot_ablation'),
#   (r'^plot/ablation/$',           'gass.public.views.display_plot_ablation'),
#   (r'^plot/mdds/$',               'gass.public.views.display_plot_mdds'),
#   (r'^plot/migration/$',          'gass.public.views.display_plot_migration'),
#   (r'^plot/conditions/$',         'gass.public.views.display_plot_conditions'),
#   (r'^export/(?P<site>\w{3})$',   'gass.public.views.export_all_records')
    )

if settings.DEBUG:
    urlpatterns += patterns('',
    (r'^gass/media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
    )
