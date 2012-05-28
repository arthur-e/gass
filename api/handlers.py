import re, datetime, time
from django.utils import simplejson as json
from django.db.models import Avg, Max, Min, StdDev
from django.db.models.fields import FieldDoesNotExist
from django.core.exceptions import FieldError
from django.core.cache import cache
from piston.handler import BaseHandler
from piston.utils import rc, require_mime, require_extended, validate
from bering.models import *

class APIHandler(BaseHandler):
    '''
    An abstract base class intended to be used in place of BaseHandler.
    '''
    def _respond_(self, template, message):
        '''
        A helper for the entirely too verbose process of writing rc messages.
        '''
        response = template
        response.write(message)
        return response


