import os, sys
import datetime, re, csv
import logging
logger = logging.getLogger('loading')

sys.path.append('/usr/local/dev/gass/')

try:
    os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
    import settings as settings # Assumed to be in the same directory.

except ImportError:
    sys.stderr.write("Couldn't find the Django settings file\n")
    sys.exit(1)

try:
    from django.db.utils import IntegrityError

except ImportError:
    from django.db import IntegrityError

except:
    sys.stderr.write("Couldn't import the IntegrityError class\n")
    sys.exit(1)

from django.core.management import setup_environ
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.gis.geos import *
from gass.bering.models import *
from gass.bering.utils import *

class Command(BaseCommand):
    args = '<site site...>'
    help = 'Loads all available data from as many stations as <site> names given'

    def handle(self, *args, **options):
        for site in args:
            try:
                station = Station.objects.get(site__exact=site)
            except ObjectDoesNotExist:
                logger.error("Command load_station_data called with an invalid <site> name")
                return False

            if not station.operational:
                logger.info("Skipping data import for site %s because it is flagged as not operational" % site)
                return False

            # Finally, load the data for that station
            self.load(station)


    def load(self, station):
        model = Ablation
        model_fields = model().get_field_names()

        # Maps field names in CSV to proper field names
        aliases = {
            'valid': 'valid',
            'sats': 'sats',
            'hdop': 'hdop',
            'time': 'time',
            'date': 'date',
            'lat': 'lat',
            'long': 'lng', # Name long is generally a reserved word
            'alt': 'elev',
            'range': 'rng_cm', # Name range is a reserved word in Python
            'topl': 'above',
            'botl': 'below',
            'wind': 'wind_spd',
            'temp': 'temp_C', # Name temp is generally a reserved word
            'batt': 'volts'
        }

        logger.info("Starting data import for site %s at %s" % (station.site,
            str(datetime.datetime.now())))

        if station.single_file:
            reader = csv.reader(open(station.upload_path, 'rb'),
                delimiter=',', quotechar='"')
            for line in reader:
                l = reader.line_num # Lines start numbering at 1, not 0
                if line == []:
                    line = reader.next() # Check for empty lines

                if l == 1:
                    header = line # Get field names
                    line = reader.next() # Move on to the first line of data

                data_dict = {
                    'site': station
                }
                for field in header:
                    value = line[header.index(field)] # The value for that field
                    # Catch empty values that should be null
                    if len(value) == 0 or value == '_':
                        if model._meta.get_field(aliases[field.lower()]).null:
                            data_dict[aliases[field.lower()]] = None

                    else:
                        data_dict[aliases[field.lower()]] = value

                data_obj = model(**data_dict) # Create a model instance
                data_obj.clean(tzinfo=UTC()) # Perform initial validation
                try: # Check to see if the record already exists
                    model.objects.get(datetime__exact=data_obj.datetime)

                except ObjectDoesNotExist:
                    data_obj.save() # Save the record to the database only if it doesn't already exist
                    logger.debug("Saved record of site %s with timestamp %s [Saved]" % (station.site, data_obj.datetime))

        else:
            logger.warn("Support for multiple file uploads not implemented; it is expected that data are aggregated in a single file")
