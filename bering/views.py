import datetime, csv
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import cache_page
from bering.models import *

@cache_page(60 * 60) # Cache page for 1 hours
def export_all_records(request, site):
    '''
    Export all records (entire history) for a given data source in CSV format;
    this view generates a CSV file.

    Keyword arguments:
    source  -- The data source all records are requested from;
                acceptable values are 'b01' and 'b02'
    start   -- The starting date of the time series to export;
                dates should be in the format 'YYYY-MM-DD' with leading zeroes
    end     -- The ending date of the time series to export;
                dates should be in the format 'YYYY-MM-DD' with leading zeroes
    '''
    average_window = 6 # Length of window to average by
    if average_window % 2 == 0:
        average_window = average_window - 1

    # TODO: If it is determined greater efficiency is needed, consider
    #   modifying this view so that it generates a CSV file on the server;
    #   a cronjob could call this function at a regular interval, and
    #   Apache could serve the "cached" file when requested

    models = {
        'b01': B1Ablation,
        'b02': B2Ablation,
        'b04': B4Ablation,
        'b06': B6Ablation,
        't01': T1Ablation
        }
    model = models[site]
    response = HttpResponse(mimetype='text/csv')
    history = []
    response['Content-Disposition'] = 'attachment; filename=' + site + '_all_records.csv'

    # These are the "pretty names" of the fields written to first row
    fields = ['Satellites', 'HDOP', 'Time(UTC)', 'Date(UTC)', 'DateTime(UTC)',
        'Latitude(N)', 'Longitude(W)', 'GPSValid',
        'AcousticRange(cm)', 'OpticalRange(cm)', 'AblationValid',
        'Irradiance', 'Reflectance', 'WindSpeed(m/s)', 'Temperature (C)',
        'Voltage(V)']

    if model == B2Ablation:
        fields.insert(7, 'Elevation')

    fields = tuple(fields)

    for record in model.objects.all().order_by('datetime'):
        sequence = [] # Create a blank sequence to append to
        sequence.append(record.satellites)
        sequence.append(record.hdop)
        sequence.append(record.time)
        sequence.append(record.date)
        sequence.append(record.datetime)
        sequence.append(record.lat)
        sequence.append(record.lng)
        if model == B2Ablation:
            sequence.append(record.elev)
        sequence.append(record.gps_ok)
        sequence.append(record.acoustic_range_cm)
        sequence.append(record.optical_range_cm)
        sequence.append(record.ablation_ok)
        sequence.append(record.top_light)
        sequence.append(record.bottom_light)
        sequence.append(record.wind_m_s)
        sequence.append(record.temp_C)
        sequence.append(record.voltage)
        history.append(sequence) # Append all fields to the history

    csv_writer = csv.writer(response, dialect='excel')
    csv_writer.writerow(fields)
    csv_writer.writerows(history)
    
    return response
