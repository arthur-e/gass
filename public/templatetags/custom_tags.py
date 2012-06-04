from django import template
from decimal import Decimal

register = template.Library()

def convert(value, conversion):
    '''Converts the units of a numeric input from one unit to another'''
    c = conversion

    weights = {
        'm/s_knots': 1.943844,
        'degC_degF': 1.8,
        'hPa_mmHg': 0.750061561,
        'minLat_m': 1856.9, # The length of 1 arcminute at 60 degrees N
        'minLong_m': 930.0,
        'cm_in': 0.3937
        }

    constants = {
        'm/s_knots': 0.0,
        'degC_degF': 32.0,
        'hPa_mmHg': 0.0,
        'minLat_m': 0.0,
        'minLong_m': 0.0,
        'cm_in': 0.0,
        }

    if isinstance(value, Decimal):
        new_value = Decimal(str(constants[c])) + (value*Decimal(str(weights[c])))
    else:
        new_value = constants[c] + (value*weights[c])
    return new_value

register.filter('convert', convert)
