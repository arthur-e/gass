from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from public.models import News
from bering.models import Station, Ablation

def display_index(request):
    '''
    localhost/gass/
    '''
    sites = Station.objects.filter(operational__exact=True).order_by('site')

    # Get the latest ablation observation for each site
    obs = []
    for each in sites:
        obs.append(each.ablation_set.latest())

    return render_to_response('index.html', {
        'news': News.objects.all().order_by('-timestamp')[0:5],
        'observations': obs
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


def display_team(request):
    '''
    localhost/gass/team/
    '''
    return render_to_response('team.html', {})
