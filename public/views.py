import datetime
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import cache_page
from public.models import News
from bering.models import Station, Ablation

def load_defaults():
    '''
    The base.html template requires this load routine.
    '''
    sites = Station.objects.all().order_by('site')
    stations = []
    campaigns = []
    then = datetime.datetime(1900,1,1,0,0,0)
    for each in sites:
        try:
            latest_campaign = each.campaign_set.latest()
            latest_ablation = each.ablation_set.latest()
            latest_ablation.operational = each.operational

        except ObjectDoesNotExist:
            return {
                'stations': [],
                'campaigns': [],
                'then': then
            }

        # Check for site visits where height of sensor may have changed
        try:
            last_visit = latest_campaign.site_visits.latest()
            if last_visit.ablato_adjusted:
                # Subtract sensor height when last adjusted
                latest_ablation.rng_cm -= last_visit.ablation_height_cm

            else:
                # Subtract sensor height when sensor was installed
                latest_ablation.rng_cm -= latest_campaign.site.init_height_cm

        except ObjectDoesNotExist:
            # No visits? Subtract sensor height when sensor was installed
            latest_ablation.rng_cm -= latest_campaign.site.init_height_cm

        # Get the latest ablation observation for each site
        stations.append(latest_ablation)

        # Get a list of field campaigns and latest observational data
        campaigns.append({
            'region': latest_campaign.region,
            'site': latest_campaign.site,
            'lat': latest_ablation.lat,
            'lng': latest_ablation.lng,
            'datetime': latest_ablation.datetime,
            'gps_valid': latest_ablation.gps_valid,
            'rng_cm_valid': latest_ablation.rng_cm_valid,
            'operational': each.operational
        })

        if latest_ablation.datetime > then:
            then = latest_ablation.datetime

    return {
        'stations': stations,
        'campaigns': campaigns,
        'then': then
    }


def display_index(request):
    '''
    localhost/gass/
    '''
    data_dict = load_defaults()
    data_dict['news'] = News.objects.all().order_by('-timestamp')[0:5]
    data_dict['now'] = datetime.datetime.now()
    return render_to_response('index.html', data_dict)


def display_about(request):
    '''
    localhost/gass/about/
    '''
    return render_to_response('about.html', load_defaults())


def display_access(request):
    '''
    localhost/gass/access/
    '''
    return render_to_response('data.html', load_defaults())


def display_instruments(request):
    '''
    localhost/gass/hardware/
    '''
    return render_to_response('instruments.html', load_defaults())


def display_team(request):
    '''
    localhost/gass/team/
    '''
    return render_to_response('team.html', load_defaults())
