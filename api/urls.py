from django.conf.urls.defaults import *
from piston.resource import Resource
from handlers import *

urlpatterns = patterns('',
    url('^ablation(\.(?P<emitter_format>.+))$', Resource(AblationHandler)),
)

