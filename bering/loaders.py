# Use print() function instead of print statement
from __future__ import print_function
from decimal import *
from django.core.management import setup_environ
import datetime, os, sys

os.environ["DJANGO_SETTINGS_MODULE"] = "gass.settings"
sys.path.append('/usr/local/project')
import gass
from gass.bering.models import B1Ablation, B2Ablation

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

class UTC(datetime.tzinfo):
    '''UTC'''
    def utcoffset(self, dt):
        return datetime.timedelta(0)
    def tzname(self, dt):
        return 'UTC'
    def dst(self, dt):
        return datetime.timedelta(0)


class Coord:
    '''An abstract coordinate class'''
    def __init__(self, value=0.0):
        self.set_encoded_value(value)


class Date:
    def __init__(self, value):
        self.set_encoded_value(value)
    def set_encoded_value(self, val):
        '''Assumes val is a string of the form DDMMYY'''
        l = len(val)
        if val.find('.') is not -1:
            val = val[:val.find('.')] # Find and exclude fractional part
        val = val.rjust(6, '0') # Embed time stamp in string of zeroes, length 6
        self.day = int(val[0:2])
        self.month = int(val[2:4])
        self.year = int('20' + val[4:6])
        self.value = datetime.date(day=self.day, month=self.month, year=self.year)

class Time:
    def __init__(self, value):
        self.set_encoded_value(value)
    def set_encoded_value(self, val):
        '''Assumes val is a string of the form HHMMSS.SSS'''
        if val.find('.') is not -1:
            val = val[:val.find('.')] # Find and exclude fractional part
        val = val.rjust(6, '0') # Embed time stamp in string of zeroes, length 6
        self.hour = int(val[0:2])
        self.minute = int(val[2:4])
        self.second = int(val[4:6])
        self.value = datetime.time(hour=self.hour, minute=self.minute, second=self.second, tzinfo=UTC())


class Lat(Coord):
    '''A latitude coordinate'''
    def set_encoded_value(self, val):
        '''
        Assumption is that val is in DDMM.SS form where DD is the number of
        degrees of North latitude and MM.SS is the decimal minutes
        '''
        self.value = int(val[0:2]) + Decimal(val[2:])/60


class Lng(Coord):
    '''A longitude coordinate'''
    def set_encoded_value(self, val):
        '''
        Assumption is that val is in DDDMM.SS form where DD is the number of
        degrees of West longitude and MM.SS is the decimal minutes
        '''
        self.value = int(val[0:3]) + Decimal(val[3:])/60


def load_from_csv(path, station_id=None, tzone=EDT()):
    '''
    Loads GASS data in bulk from a CSV file.
    <path>          {String}            The path to the CSV file
    <station_id>    {String}            The station ID e.g. "b01"
    <tzone>         {datetime.tzinfo}   A time zone representation (defaults to
                                        EDT)
    '''
    if station_id is None and model is None:
        raise TypeError("load_from_csv() requires that at least one of the arguments, <station_id> or <model>, be provided")

    if station_id is not None and model is None:
        model = MODELS[station_id]

    else: # We can look up the buoy ID for you if a model was specified
        station_id = lookup_uid(model)

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
                if model._meta.get_field(field.lower()).null:
                    data_dict[field.lower()] = None

            else:
                data_dict[field.lower()] = value

        data_dict['asset'] = Asset.objects.get(uid__exact=station_id)

        data_obj = model(**data_dict) # Create a model instance
        data_obj.clean(tzinfo=tzone) # Perform initial validation
        try:
            model.objects.get(timestamp__exact=data_obj.timestamp) # Check to see if the record already exists

        except ObjectDoesNotExist:
            data_obj.save() # Save the record to the database only if it doesn't already exist
            buoy_logger.debug("Saved record of %s with timestamp %s [Saved]" % (model._meta.object_name, data_dict['timestamp']))


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
