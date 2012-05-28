from django.conf.urls.defaults import *
from piston.resource import Resource
from handlers import *

urlpatterns = patterns('',
    url('^ablation$', Resource(AblationHandler), {'emitter_format': 'ext-json'}),
)

