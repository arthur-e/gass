# Use print() function instead of print statement
from __future__ import print_function
import datetime, os, sys, csv logging
from decimal import *

from django.core.management import setup_environ
os.environ["DJANGO_SETTINGS_MODULE"] = "gass.settings"
sys.path.append('/usr/local/dev/')

from gass.bering.models import Ablation
from gass.bering.utils import *

logger = logging.getLogger('loading')

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
    'range': 'range_cm', # Name range is a reserved word in Python
    'topl': 'above',
    'bottom': 'below',
    'wind': 'wind_spd',
    'temp': 'temp_C', # Name temp is generally a reserved word
    'batt': 'volts'
}

# Data dictionary describing field name, position in CSV, and data type
fields = {
    'satellites':       [1,     int],
    'hdop':             [2,     float],
    'time':             [3,     Time], # See Time class above
    'date':             [4,     Date], # See Date class above
    'datetime':         [None,  datetime.datetime], # See datetime module
    'lat':              [5,     Lat], # Convert to decimal degrees
    'lng':              [6,     Lng], # Convert to decimal degrees
    'acoustic_range_cm':[7,     Decimal], # See decimal module
    'optical_range_cm': [8,     Decimal],
    'top_light':        [9,     int],
    'bottom_light':     [10,    int],
    'wind_m_s':         [11,    Decimal],
    'temp_C':           [12,    Decimal],
    'voltage':          [13,    float]
    }

def load_from_csv(path, station_id, tzone=UTC()):
    '''
    Loads GASS data in bulk from a CSV file.
    <path>          {String}            The path to the CSV file
    <station_id>    {String}            The station ID e.g. "b01"
    <tzone>         {datetime.tzinfo}   A time zone representation (defaults to
                                        EDT)
    '''
    model = Ablation
    reader = csv.reader(open(path, 'rb'), delimiter=',', quotechar='"')
    for line in reader:
        l = reader.line_num # Lines start numbering at 1, not 0
        if line == []:
            line = reader.next() # Check for empty lines

        if l == 1:
            header = line # Get field names
            line = reader.next() # Move on to the first line of data

        data_dict = {}
        for field in header:
            value = line[header.index(field)] # The value for that field
            # Catch empty values that should be null
            if len(value) == 0 or value == '_':
                if model._meta.get_field(aliases[field.lower()]).null:
                    data_dict[aliases[field.lower()]] = None

            else:
                data_dict[aliases[field.lower()]] = value

#        data_dict['lat'] = Lat(data_dict['lat']).value
#        data_dict['lng'] = Lng(data_dict['lng']).value
#        data_dict['date'] = Date(data_dict['date']).value
#        data_dict['time'] = Time(data_dict['time']).value

        data_obj = model(**data_dict) # Create a model instance
        data_obj.clean(tzinfo=tzone) # Perform initial validation
        try:
            model.objects.get(datetime__exact=data_obj.datetime) # Check to see if the record already exists

        except ObjectDoesNotExist:
            data_obj.save() # Save the record to the database only if it doesn't already exist
            logger.debug("Saved record of %s with timestamp %s [Saved]" % (model._meta.object_name, data_dict['datetime']))


def append_to_log(entry):
    '''Adds an entry to the log'''
    # Check to see that the directory can be read from
    if os.access(log_dir, os.W_OK):
        with open(log_dir + log_file, mode='a') as log:
            now = datetime.datetime.now()
            print(now.strftime('%Y-%m-%d %H:%M') + ' -- ' + entry, file=log)


def quality_check(data_dict, last_data_dict, filename, line):
    '''
    Returns True if the data are of sufficient quality to be included in the
    database, False to reject the data and not create a record.
    '''
    if last_data_dict and 'datetime' in data_dict.keys():
        datetime_diff = abs((data_dict['datetime'] - last_data_dict['datetime']).seconds)
        acoustic_range_cm_diff = abs(data_dict['acoustic_range_cm'] - last_data_dict['acoustic_range_cm'])

        # Test for sufficient constellation
        if data_dict['satellites'] < 3:
            append_to_log('Line %d from filename %s failed quality check: Insufficient satellites' % (line, filename))
            return False # Accurate measurements require at least 3 satellites

        # No test for hdop; do that in database queries where concerned

        # Test for sufficient separation in time between measurements
        elif datetime_diff < 2400:
            # append_to_log('%s: %s' % (line, last_data_dict['datetime'].isoformat()))
            # append_to_log('%s: %s' % (line, data_dict['datetime'].isoformat()))
            append_to_log('Line %d from filename %s failed quality check: Not an independent measurement (in time) [datetime_diff = %s]' % (line, filename, datetime_diff))
            return False # Measurements must be at least 40 minutes apart

        # Test for obviously bogus acoustic measurements
        elif data_dict['acoustic_range_cm'] > Decimal(str(600.0)):
            # append_to_log('%s: %s' % (line, str(data_dict['acoustic_range_cm'])))
            append_to_log('Line %d from filename %s failed quality check: Range above 600 cm [acoustic_range_cm = %s]' % (line, filename, str(data_dict['acoustic_range_cm'])))
            return False # Measurements above 600 are probably "corked"

        # Test for likely bogus acoustic measurements
        elif datetime_diff < 4200 and acoustic_range_cm_diff > Decimal(str(10.0)) and last_data_dict['acoustic_range_cm'] < Decimal(str(600.0)):
            # append_to_log('%s: %s and %s cm' % (line, last_data_dict['datetime'].isoformat(), str(last_data_dict['acoustic_range_cm'])))
            # append_to_log('%s: %s and %s cm' % (line, data_dict['datetime'].isoformat(), str(data_dict['acoustic_range_cm'])))
            append_to_log('Line %d from filename %s failed quality check: Change in range from last measurement more than 10 cm [datetime_diff = %s; acoustic_range_cm_diff = %s]' % (line, filename, datetime_diff, acoustic_range_cm_diff))
            return False
            # Closely-separated measurements in time (less than 70 minutes)
            #   with more than 10 cm melt are likely invalid

        else:
            return True

    else:
        return False


def import_from_csv(filename, model):
    '''Imports GASS data from a given CSV file for a given data model'''
    with open(filename, mode='r') as csv:
        strips = '" \n' # Disallowed characters to strip
        all_lines = [] # List to contain the lines of the stream file
        last_data_dict = {} # Empty data dictionary to hold previous record

        for line in csv:
            line = line.replace('**.*','').replace(' ','').replace('"','').replace("'", '').strip(strips) # Remove unwanted characters
            values = line.split(',') # Split on commas to separate values
            all_lines.append(values) # Add to list of lines

    l = 0 # Line counter
    for line in all_lines:
        data_dict = {} # Empty data dictionary representing Model instance

        if line[0] != "V" and line[5] != "" and line[6] != "":

            for field in fields.items():
                # Method items() returns a list of (key, value) tuples;
                #   in this case, key is the field name and value is a list with:
                #   [pos, type] where pos is the field's position in csv, type is
                #   the required data type for the database

                if field[1][0]:
                    # If there's a valid position given (if the field is a raw field)
                    field_name = field[0] # This is the name of the field
                    value = line[field[1][0]] # This is the raw data value
                    required_type = field[1][1] # This is the data type it should be

                if value is not '':
                    # We want to insert null into the database, not empty strings
                    if isinstance(value, required_type) or required_type == datetime.datetime:
                        # If the value is already of the required type or that type is
                        #   a datetime.datetime() instance...
                        data_dict[field_name] = value

                    else:
                        # Convert the value if it isn't of the required type
                        if required_type in [Lat, Lng, Date, Time]:
                            data_dict[field_name] = required_type(value).value
                        else:
                            data_dict[field_name] = required_type(value)
                        #TODO: Make Lat, Lng, Date, and Time classes just like Python built-in types int, float, etc...

                else:
                    data_dict[field_name] = None # Insert a null value if none available

        # Finally, we calculate the value of the datetime field
        if 'date' in data_dict.keys() and 'time' in data_dict.keys():
            data_dict['datetime'] = datetime.datetime.combine(data_dict['date'], data_dict['time'])

        else:
            append_to_log('No date or time information associated with the record!')

        # Save the new record only if it meets quality standards
        if quality_check(data_dict, last_data_dict, filename, l):
            this = model(**data_dict) # Create a model instance
            try:
                this.save() # UPDATES if primary key is found, INSERTS otherwise
                # print("Saving line %s to the database..." % l)
            except:
                append_to_log('Failed to save record from filename %s with date %s and time %s' % (filename, data_dict['date'].isoformat(), data_dict['time'].isoformat()))

        last_data_dict = data_dict # Save this data dictionary for next time
        l += 1


if __name__ == "__main__":
    # In case the script is run from a terminal...
    setup_environ(gass.settings) # Have Django set up environmental variables

    # Must use trailing slashes for directories!
    origin_dir = '/netfs/net/nas1/data/nonitar/IridiumData/' # Directory where data are stored
    log_dir = '/usr/local/project/gass/bering/'
    log_file = 'loaders_log.txt' # Log file
    b1 = {
        'filename': '300234010623080.csv', # B01 Iridium modem serial number
        'model': B1Ablation
        }
    b2 = {
        'filename': '300234010624080.csv', # B02 Iridium modem serial number
        'model': B2Ablation
        }
    datasets = [b1, b2]
    files = os.listdir(origin_dir) # List of actual files

    # Check to see that the directory can be read from
    if not os.access(origin_dir, os.R_OK):
        append_to_log('No access to the specified file directory.')

    # Check to see that the files exist
    for each in datasets:

        if each['filename'] not in files:
            append_to_log('File "' + each['filename'] + '" not found.')

        else:
            import_from_csv(origin_dir + each['filename'], each['model'])
