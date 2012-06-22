import re, math
from django.contrib.gis.db import models
from gass.bering.utils import *

class Station(models.Model):
    '''
    Ablatometer station, idealized i.e. designation B01 is re-used each year.
    '''
    site = models.CharField(max_length=255, unique=True)
    operational = models.BooleanField(help_text="Indicates that the station data should be reported")
    upload_path = models.TextField(help_text="File system path to the file or directory where data are uploaded")
    single_file = models.BooleanField(help_text="Indicates that data uploads are aggregate in a single file, specified by the record's upload_path", default=True)
    utc_offset = models.IntegerField(help_text="The UTC offset, in hours, positive or negative")
    init_height_cm = models.FloatField(verbose_name='initial sensor height in cm', help_text="The initial height of the instrument box, in centimeters")

    def __unicode__(self):
        return str(self.site)


    def __str__(self):
        return str(self.site)


    def clean(self, *args, **kwargs):
        '''
        Validates and/or cleans input before saving to the databse.
        '''
        # Force site names to be lowercase
        self.site = str(self.site).lower()


class SiteVisit(models.Model):
    '''
    An in situ field visit, particular notable where ablatometer height was
    adjusted manually.
    '''
    site = models.ForeignKey(Station, to_field='site')
    datetime = models.DateTimeField(help_text="Date and time of site visit, in UTC")
    ablato_adjusted = models.BooleanField(verbose_name='ablatometer was adjusted', default=True)
    ablato_height_cm = models.FloatField(verbose_name='ablatometer height after adjustment in cm', blank=True, null=True)
    notes = models.TextField()

    class Meta:
        get_latest_by = 'datetime'


    def __unicode__(self):
        return '%s: %d (%s)' % (self.site.upper(), self.ablato_height_cm,
            self.datetime.strftime('%Y-%m-%d %H:%M:%S'))


class Campaign(models.Model):
    '''
    Ablation measurement campaign.
    '''
    site = models.ForeignKey(Station, to_field='site')
    season = models.IntegerField(help_text="The year the ablatometer was deployed")
    deployment = models.DateField(help_text="Date of the deployment")
    recovery = models.DateField(help_text="Date of recovery")
    region = models.CharField(max_length=255, help_text="General description of the deployed location e.g. Tashalich Arm")
    has_uplink = models.BooleanField(help_text="Indicates that the instrument was equipped with a satellite uplink")
    site_visits = models.ManyToManyField(SiteVisit, blank=True, null=True)

    class Meta:
        get_latest_by = 'deployment'
        unique_together = ('site', 'season')


    def __unicode__(self):
        return '%s (%d)' % (self.site_id.upper(), self.season)


class Ablation(models.Model):
    '''
    Ablation measurement.
    '''
    objects = models.GeoManager()
    valid = models.BooleanField(editable=False, help_text="Indiates whether the observation record is valid (this flag set by instrument only)")
    site = models.ForeignKey(Station, to_field='site')
    sats = models.IntegerField(verbose_name='satellites', help_text='Number of satellites')
    hdop = models.FloatField(help_text='Horizontal dilution of precision (HDOP)', null=True)
    time = models.TimeField(help_text="This is a naive time, not time-zone aware")
    date = models.DateField()
    datetime = models.DateTimeField(help_text='Date and time of measurement from GPS')
    lat = models.FloatField(help_text='Latitude (Deg, Dec. Min. N)')
    lng = models.FloatField(help_text='Longitude (Deg, Dec. Min. W)')
    gps_valid = models.BooleanField(help_text="Indicates whether the GPS measurements are valid", default=True)
    elev = models.FloatField(verbose_name='altitude (m)')
    rng_cm = models.FloatField(verbose_name='acoustic range (cm)')
    rng_cm_valid = models.BooleanField(help_text="Indicates whether the range measurement is valid", default=True)
    above = models.IntegerField(verbose_name='irradiance')
    below = models.IntegerField(verbose_name='reflectance')
    wind_spd = models.FloatField(verbose_name='wind speed (m/s)')
    temp_C = models.FloatField(verbose_name='temperature (C)')
    volts = models.FloatField(verbose_name='battery voltage (V)')
    point = models.PointField(srid=4326)


    class Meta:
        get_latest_by = 'datetime'


    def __unicode__(self):
        return '[%s] %s at %s' % (str(self.site_id),
            str(self.date), str(self.time))


    @classmethod
    def get_field_names(self, string=None):
        '''
        Returns a list of field names that match an optional string that can be
        parsed as a regular expression.
        '''
        names = self._meta.get_all_field_names()
        if string:
            return [name for name in names if re.compile(string).match(name) != None]

        else:
            return [name for name in names]


    @classmethod
    def get_base_field_names(self):
        return ('site_id', 'sats', 'hdop', 'datetime', 'lat', 'lng', 'elev',
            'rng_cm', 'above', 'below', 'wind_spd', 'temp_C', 'volts')


    def get_previous_record(self, *args, **kwargs):
        '''
        '''
        td = datetime.timedelta(hours=1)
        foretime = self.datetime + td # An hour later
        backtime = self.datetime - td # An hour earlier
        # Get a window of observations around this sorted datetime descending
        window = Ablation.objects.filter(site__exact=self.site,
            datetime__range=(backtime, foretime)).order_by('-datetime')

        # Find the first adjacent record earlier in time
        if len(window) > 1:
            for each in window:
                if each.datetime.replace(tzinfo=UTC()) < self.datetime:
                    return each

        elif len(window) == 1:
            # Only if the record is previous in time...
            if window[0].datetime.replace(tzinfo=UTC()) < self.datetime:
                return window[0]

            else: return None

        # No adjacent measurements in time
        elif len(window) == 0: return None

        else: return ValueError


    def clean(self, *args, **kwargs):
        '''
        Accepts a tzinfo keyword argument where tzinfo is an instance of
        datetime.tzinfo that can be passed to the replace() method.
        '''
        if isinstance(self.valid, str):
            if self.valid == 'A': self.valid = True
            else: self.valid = False

        if isinstance(self.lng, str):
            # For now, force the negation of longitude values (raw data don't distinguish)
            self.lng = -float(Lng(self.lng).value)

        if isinstance(self.lat, str):
            self.lat = Lat(self.lat).value

        if isinstance(self.date, str):
            self.date = Date(self.date).value

        if isinstance(self.time, str):
            # Django does not support timezone-aware times, only datetimes
            self.time = Time(self.time).value

        self.datetime = datetime.datetime.combine(self.date,
            self.time).replace(tzinfo=kwargs['tzinfo'])
        # For now, force the negation of longitude values
        self.point = 'POINT(%s %s)' % (-float(self.lng), self.lat)
        self.rng_cm = float(self.rng_cm)
        self.check_flags()


    def check_flags(self, *args, **kwargs):
        '''
        A validation procedure setting gps_valid and rng_cm_valid flags.
        '''
        last = self.get_previous_record()

        # TEST: Sufficient satellite constellation?
        if self.sats < 3:
            self.gps_valid = False
            # No test for hdop; do that in database queries where concerned

        # TEST: Obviously bogus acoustic measurements (greater than 600 cm)?
        if self.rng_cm > 600.0:
            self.rng_cm_valid = False

        try:
            if last is None: return None

        except UnboundLocalError:
            return None

        datetime_diff = abs((self.datetime - last.datetime.replace(tzinfo=UTC())).seconds)
        rng_cm_diff = self.rng_cm - last.rng_cm

        # TEST: Indpendent measurements?
        if datetime_diff < 1600:
            # Expected that measurements no more frequent than every 20 minutes
            self.gps_valid = False

        # TEST: Likely bogus acoustic measurements?
        if datetime_diff < (60*60*3) and rng_cm_diff > 5.0 and last.rng_cm < 600.0:
            # Closely-separated measurements in time (less than 3 hours)
            #   with more than 5 cm melt are likely invalid
            self.rng_cm_valid = False

        # TEST: Likely bogus acoustic measurements?
        if not last.rng_cm_valid and rng_cm_diff > 0.0:
            # The last range measurement was invalid and this one is greater
            self.rng_cm_valid = False


    def geographic_distance(self, obj):
        '''
        Calculates the distance, in meters, between the position of this
        measurement and another.
        Accepts:
            obj     {Ablation}  Another Ablation model instance
        Returns:
            {Float} The net migration, in meters, between the two observations
        '''
        lat_m_per_degree = 111412.0
        lng_m_per_degree = 55800.0
        # 111,412 m/degree of latitude at 60 degrees north latitude
        #   (from National Geospatial Intelligence Agency)
        # 55,800 m/degree of longitude at 60 degrees north latitude
        #   (from National Geospatial Intelligence Agency)
        # http://msi.nga.mil/MSISiteContent/StaticFiles/Calculators/degree.html

        lat_diff_m = abs(lat_m_per_degree*(self.lat - obj.lat))
        lng_diff_m = abs(lng_m_per_degree*(self.lng - obj.lng))

        # Simple distance estimate in meters between last and last observation
        distance_m = math.sqrt((lat_diff_m*lat_diff_m) + (lng_diff_m*lng_diff_m))
        return distance_m


class B1Ablation(models.Model):
    '''Ablation measurement at GASS B01; identical to B2Ablation model.'''
    satellites = models.IntegerField('Number of Satellites')
    hdop = models.FloatField('Dilution of Precision', null=True)
    time = models.TimeField('Time')
    date = models.DateField('Date')
    # datetime = models.DateTimeField('Date and Time', unique=True)
    # We tried making datetime unique before but that led to
    #   database errors that could not be resolved when there
    #   was an attempt to insert a duplicate record
    datetime = models.DateTimeField('Date and Time', primary_key=True)
    # By using datetime as the primary key, we ensure that:
    #   a) Duplicate records in the raw data are entered as one
    #       record with the most recent meteorological and
    #       ablation data
    #   b) When updating the database, we can pull records from
    #       a consolidated file of all existing records without
    #       fear of re-inserting records already in the database
    lat = models.DecimalField('Latitude (Deg, Dec. Min. N)', max_digits=8, decimal_places=5)
    lng = models.DecimalField('Longitude (Deg, Dec. Min. W)', max_digits=9, decimal_places=5)
    gps_ok = models.BooleanField('Position is Valid')
    acoustic_range_cm = models.DecimalField('Acoustic Range (cm)', max_digits=5, decimal_places=2)
    optical_range_cm = models.DecimalField('Optical Range (cm)', max_digits=10, decimal_places=5)
    # sensor_height = models.DecimalField('Sensor Height at Installation', max_digits=5, decimal_places=2)
    ablation_ok = models.BooleanField('Ablation is Valid')
    top_light = models.IntegerField('Irradiance)')
    bottom_light = models.IntegerField('Reflectance)')
    wind_m_s = models.DecimalField('Wind Speed (m/s)', max_digits=5, decimal_places=2)
    # temp_C is allowed to be null because negative temperature measurements
    #   currently can't be handled (hardware issue)
    temp_C = models.DecimalField('Temperature (C)', max_digits=4, decimal_places=1, null=True)
    voltage = models.FloatField('Battery Voltage (V)')

    def __unicode__(self):
        return str(self.date) + ', ' + str(self.time)


class B2Ablation(models.Model):
    '''Ablation measurement at GASS B02; almost identical to B1Ablation model (has elevation).'''
    satellites = models.IntegerField('Number of Satellites')
    hdop = models.FloatField('Dilution of Precision', null=True)
    time = models.TimeField('Time')
    date = models.DateField('Date')
    datetime = models.DateTimeField('Date and Time', primary_key=True)
    lat = models.DecimalField('Latitude (Deg, Dec. Min. N)', max_digits=8, decimal_places=5)
    lng = models.DecimalField('Longitude (Deg, Dec. Min. W)', max_digits=9, decimal_places=5)
    elev = models.DecimalField('Elevation', max_digits=4, decimal_places=1, blank=True, null=True)
    gps_ok = models.BooleanField('Position is Valid')
    acoustic_range_cm = models.DecimalField('Acoustic Range (cm)', max_digits=5, decimal_places=2)
    optical_range_cm = models.DecimalField('Optical Range (cm)', max_digits=10, decimal_places=5)
    # sensor_height = models.DecimalField('Sensor Height at Installation', max_digits=5, decimal_places=2)
    ablation_ok = models.BooleanField('Ablation is Valid')
    top_light = models.IntegerField('Irradiance)')
    bottom_light = models.IntegerField('Reflectance)')
    wind_m_s = models.DecimalField('Wind Speed (m/s)', max_digits=5, decimal_places=2)
    temp_C = models.DecimalField('Temperature (C)', max_digits=4, decimal_places=1, null=True)
    voltage = models.FloatField('Battery Voltage (V)')

    def __unicode__(self):
        return str(self.date) + ', ' + str(self.time)


class B4Ablation(models.Model):
    '''Ablation measurement at GASS B04; identical to B1Ablation model.'''
    satellites = models.IntegerField('Number of Satellites')
    hdop = models.FloatField('Dilution of Precision', null=True)
    time = models.TimeField('Time')
    date = models.DateField('Date')
    datetime = models.DateTimeField('Date and Time', primary_key=True)
    lat = models.DecimalField('Latitude (Deg, Dec. Min. N)', max_digits=8, decimal_places=5)
    lng = models.DecimalField('Longitude (Deg, Dec. Min. W)', max_digits=9, decimal_places=5)
    gps_ok = models.BooleanField('Position is Valid')
    acoustic_range_cm = models.DecimalField('Acoustic Range (cm)', max_digits=5, decimal_places=2)
    optical_range_cm = models.DecimalField('Optical Range (cm)', max_digits=10, decimal_places=5)
    # sensor_height = models.DecimalField('Sensor Height at Installation', max_digits=5, decimal_places=2)
    ablation_ok = models.BooleanField('Ablation is Valid')
    top_light = models.IntegerField('Irradiance)')
    bottom_light = models.IntegerField('Reflectance)')
    wind_m_s = models.DecimalField('Wind Speed (m/s)', max_digits=5, decimal_places=2)
    temp_C = models.DecimalField('Temperature (C)', max_digits=4, decimal_places=1, null=True)
    voltage = models.FloatField('Battery Voltage (V)')

    def __unicode__(self):
        return str(self.date) + ', ' + str(self.time)


class B6Ablation(models.Model):
    '''Ablation measurement at GASS B06; identical to B1Ablation model.'''
    satellites = models.IntegerField('Number of Satellites')
    hdop = models.FloatField('Dilution of Precision', null=True)
    time = models.TimeField('Time')
    date = models.DateField('Date')
    datetime = models.DateTimeField('Date and Time', primary_key=True)
    lat = models.DecimalField('Latitude (Deg, Dec. Min. N)', max_digits=8, decimal_places=5)
    lng = models.DecimalField('Longitude (Deg, Dec. Min. W)', max_digits=9, decimal_places=5)
    gps_ok = models.BooleanField('Position is Valid')
    acoustic_range_cm = models.DecimalField('Acoustic Range (cm)', max_digits=5, decimal_places=2)
    optical_range_cm = models.DecimalField('Optical Range (cm)', max_digits=10, decimal_places=5)
    # sensor_height = models.DecimalField('Sensor Height at Installation', max_digits=5, decimal_places=2)
    ablation_ok = models.BooleanField('Ablation is Valid')
    top_light = models.IntegerField('Irradiance)')
    bottom_light = models.IntegerField('Reflectance)')
    wind_m_s = models.DecimalField('Wind Speed (m/s)', max_digits=5, decimal_places=2)
    temp_C = models.DecimalField('Temperature (C)', max_digits=4, decimal_places=1, null=True)
    voltage = models.FloatField('Battery Voltage (V)')

    def __unicode__(self):
        return str(self.date) + ', ' + str(self.time)


class T1Ablation(models.Model):
    '''Ablation measurement at GASS T01; identical to B1Ablation model.'''
    satellites = models.IntegerField('Number of Satellites')
    hdop = models.FloatField('Dilution of Precision', null=True)
    time = models.TimeField('Time')
    date = models.DateField('Date')
    datetime = models.DateTimeField('Date and Time', primary_key=True)
    lat = models.DecimalField('Latitude (Deg, Dec. Min. N)', max_digits=8, decimal_places=5)
    lng = models.DecimalField('Longitude (Deg, Dec. Min. W)', max_digits=9, decimal_places=5)
    gps_ok = models.BooleanField('Position is Valid')
    acoustic_range_cm = models.DecimalField('Acoustic Range (cm)', max_digits=5, decimal_places=2)
    optical_range_cm = models.DecimalField('Optical Range (cm)', max_digits=10, decimal_places=5)
    # sensor_height = models.DecimalField('Sensor Height at Installation', max_digits=5, decimal_places=2)
    ablation_ok = models.BooleanField('Ablation is Valid')
    top_light = models.IntegerField('Irradiance)')
    bottom_light = models.IntegerField('Reflectance)')
    wind_m_s = models.DecimalField('Wind Speed (m/s)', max_digits=5, decimal_places=2)
    temp_C = models.DecimalField('Temperature (C)', max_digits=4, decimal_places=1, null=True)
    voltage = models.FloatField('Battery Voltage (V)')

    def __unicode__(self):
        return str(self.date) + ', ' + str(self.time)


