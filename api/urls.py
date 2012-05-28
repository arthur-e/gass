from django.conf.urls.defaults import *
from piston.resource import Resource
from handlers import *

urlpatterns = patterns('',
    #url('^ibutton$', Resource(IButtonHandler), {'emitter_format': 'ext-json'}),
)

