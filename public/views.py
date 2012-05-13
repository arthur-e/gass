from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from public.models import News

def display_index(request):
    '''
    localhost/gass/
    '''
    return render_to_response('index.html', {
        'news': News.objects.all().order_by('-timestamp')[0:5]
    })


def display_about(request):
    '''
    localhost/gass/about/
    '''
    return render_to_response('about.html', {})


def display_access(request):
    '''
    localhost/gass/access/
    '''
    return render_to_response('data.html', {})


def display_instruments(request):
    '''
    localhost/gass/hardware/
    '''
    return render_to_response('instruments.html', {})
