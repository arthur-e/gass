"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
import sys, datetime, csv
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.db.models import Avg, Max, Min, Count
from gass.bering.models import AblationMeasurement, B1Ablation, B2Ablation
from gass.bering.loaders import Lat, Lng, Date, Time
from math import sqrt
from decimal import Decimal
from fractions import Fraction

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 2)

__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}

def ablation_rate(model, raw_values, hours):
    fields = ('datetime', 'acoustic_range_cm')
    raw_values = model.objects.values(*fields).order_by('datetime')

    # Find the latest measurement
    late_date = model.objects.all().aggregate(Max('datetime'))
    latest = model.objects.exclude(hdop__gte=5).filter(datetime__exact=late_date['datetime__max'])[0]

    # Find the first measurement
    first_date = model.objects.all().aggregate(Min('datetime'))
    first = model.objects.exclude(hdop__gte=5).filter(datetime__exact=first_date['datetime__min'])[0]

    # Use raw values for simple ablation calculation
    ablation_cm = raw_values[len(raw_values)-1]['acoustic_range_cm']
    ablation_cm -= first.acoustic_range_cm # Remove baseline

    # Grab an ablation measurement 24 hours ago (60 s * 60 min * 24 hrs)
    target_date = latest.datetime - datetime.timedelta(seconds=60*60*hours)
    previous_value = model.objects.values(*fields).filter(datetime__gte=target_date)[0]['acoustic_range_cm']
    previous_value -= first.acoustic_range_cm # Remove baseline

    if previous_value:
        # Get the ablation rate for 12 hours, doubled for an estimated daily rate
        multiplier = Decimal('24.0')/hours # We want a daily rate, regardless of time offset
        ablation_rate_cm_per_day = (ablation_cm - previous_value)*multiplier

        if ablation_rate_cm_per_day > 20 or ablation_rate_cm_per_day < 1:
            print ablation_cm_per_day, hours
            ablation_rate_cm_per_day = ablation_rate(model, raw_values, hours*2)

    elif first.acoustic_range_cm and latest.acoustic_range_cm:
        # If there's a problem with the daily calculation above, do it the old way
        time_offset = latest.datetime - first.datetime

        if time_offset:
            ablation_rate_cm_per_day = (latest.acoustic_range_cm - first.acoustic_range_cm)/time_offset.days

        else:
            ablation_rate_cm_per_day = 0

    else:
        ablation_rate_cm_per_day = 0

    return ablation_rate_cm_per_day

def remap(hashing):
    '''Create a dictionary for each value from a series of lists.'''
    records = []
    keys = hashing.keys()
    number_of_records = len(hashing[keys[0]]) # Better be the same for all keys
    for key in keys:
        if len(hashing[key]) != number_of_records:
            return KeyError("Each list in the input dictionary must have the same length.")

    i = 0 # Initialize counter
    while i < number_of_records:
        dictionary = {}
        for key in keys:
            dictionary[key] = hashing[key][i]
        records.append(dictionary)
        i += 1 # Increment counter

    return records
            

def sequence(listing):
    '''Create a list for each key in a dictionary.'''
    dictionary = {}

    for key in listing[0].keys():
        dictionary[key] = [] # Initalize data_dict with the field names

    for each in listing:
        # For each dictionary...

        for item in each.items():
            # For each (key, value) pair...
            dictionary[item[0]].append(item[1]) # Sequence the values

    return dictionary

def weighted_moving_average(window, records, shape='triangle', fields=None):
    '''
    Calculates a weighted moving average for a list of values. This function
    can also do simple (rectangular) moving averages (SMA).
    Accepts:
        window  {Integer}   Number of points to average on; length of SMA window
        records {List}      Records to perform the average on
        shape   {String}    Shape of the window; 'rectangle' or 'triangle'
        fields  {List}      Name of key(s) to grab value from (if records is a
                            list of dictionaries)
    Returns:
        {List}  List of "smoothed" values or of dictionaries with smoothed values
    '''
    if shape == 'triangle':

        if window % 2 == 0:
            window - 1 # Make sure window is an odd number (required)

        averaged_records = []
        ramps = [] # Scales for the "sides" of the triangular window
        for num in range(1, (window/2) + 1):
            ramps.append(Decimal(str(float(Fraction(num, (window/2) + 1)))))

        if sum(ramps) != Decimal('1.0'):
            return ValueError("Non-unity for sum of weights in triangular window.")

        i = 0 # Initialize counter for records
        while i < len(records):
            start = i-(window/2) # Rounds down always
            end = i+(window/2) + 1 # Grab edge of next bin (requires +1)
            if start < 0:
                pass # Exclude edge effects by truncating the series
            elif end >= len(records):
                pass # Exclude edge effects at the end also
            else:
                early_subset = records[start:i] # Ascending side of triangle
                late_subset = records[i+1:end] # Descending side of triangle

                j = 0 # Initialize counter for early_subset
                while j < len(early_subset):
                    if fields:
                        for field in fields:
                            early_subset[j][field] = early_subset[j][field]*ramps[j]
                    else:
                        early_subset[j] = early_subset[j]*ramps[j] # Scale the backwards-looking view
                    j += 1 # Increment counter for early_subset

                k = 0 # Initialize counter for late_subset
                ramps.reverse() # We're descending in scales for symmetry
                while k < len(late_subset):
                    if fields:
                        for field in fields:
                            early_subset[k][field] = late_subset[k][field]*ramps[k]
                    else:
                        early_subset[k] = late_subset[k]*ramps[k] # Scale the forwards-looking view
                    k += 1 # Increment counter for late_subset

                if fields:

                    # Include all fields, regardless of whether they were averaged on
                    data_dict = records[i].copy()

                    for field in fields:
                        # If the field is one that was averaged on...
                        early_values = []
                        late_values = []
                        for d in early_subset:
                            early_values.append(d.get(field))
                        for d in late_subset:
                            late_values.append(d.get(field))
                        data_dict[field] = (sum(early_values) + sum(late_values) + records[i][field])/3
                    # Return an average of the backwards, forwards-looking view and
                    #   value at that point
                    averaged_records.append(data_dict)

                else:
                    averaged_records.append((sum(early_subset) + sum(late_subset) + records[i])/3)

            i += 1 # Incerement counter for records
            ramps.reverse()
        return averaged_records

    else:
        return simple_moving_average(window, records)

