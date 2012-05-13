from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.core.cache import cache
from django.views.decorators.cache import cache_page

def display_index(request):
    '''
    localhost/gass/
    '''
    return render_to_response('index.html', {})
