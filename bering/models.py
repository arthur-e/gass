from django.contrib.gis.db import models

class Ablation(models.Model):
    '''
    Ablation measurement from the 2012 campaign.
    '''
    STATIONS = (
        ('t01', 'T01'),
        ('b01', 'B01'),
        ('b02', 'B02'),
        ('b03', 'B03'),
        ('b04', 'B04'),
        ('b06', 'B06')
    )
    objects = models.GeoManager()
    valid = models.BooleanField()
    site = models.CharField(max_length=255, choices=STATIONS)
    sats = models.IntegerField(verbose_name='satellites', help_text='Number of satellites')
    hdop = models.FloatField(help_text='Horizontal dilution of precision (HDOP)', null=True)
    time = models.TimeField()
    date = models.DateField()
    datetime = models.DateTimeField(help_text='Date and time of measurement from GPS')
    lat = models.FloatField(help_text='Latitude (Deg, Dec. Min. N)')
    lng = models.FloatField(help_text='Longitude (Deg, Dec. Min. W)')
    elev = models.FloatField(verbose_name='altitude (m)')
    range_cm = models.FloatField(verbose_name='acoustic range (cm)')
    above = models.IntegerField(verbose_name='irradiance')
    below = models.IntegerField(verbose_name='reflectance')
    wind_spd = models.FloatField(verbose_name='wind speed (m/s)')
    temp_C = models.FloatField(verbose_name='temperature (C)')
    volts = models.FloatField(verbose_name='battery voltage (V)')
    point = models.PointField(srid=4326)

    def __unicode__(self):
        return str(self.date) + ', ' + str(self.time)


    def clean(self, *args, **kwargs):
        '''
        Accepts a tzinfo keyword argument where tzinfo is an instance of
        datetime.tzinfo that can be passed to the replace() method.
        '''
        if isinstance(self.valid, str):
            if self.valid == 'A': self.valid = True
            else: self.valid = False

        if isinstance(self.lng, str):
            self.lng = Lng(self.lng).value

        if isinstance(self.lat, str):
            self.lat = Lat(self.lat).value

        if isinstance(self.date, str):
            self.date = Date(self.date).value

        if isinstance(self.time, str):
            self.time = Time(self.time).value.replace(tzinfo=kwargs['tzinfo'])

        self.datetime = datetime.datetime.combine(self.date, self.time).replace(tzinfo=kwargs['tzinfo'])


class B1Ablation(models.Model):
    '''2011 ablation measurement at GASS B1; identical to B2Ablation model.'''
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
    acoustic_range_cm = models.DecimalField('Acoustic Range (cm)', max_digits=5, decimal_places=2)
    optical_range_cm = models.DecimalField('Optical Range (cm)', max_digits=10, decimal_places=5)
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
    '''2011 ablation measurement at GASS B2; identical to B1Ablation model.'''
    satellites = models.IntegerField('Number of Satellites')
    hdop = models.FloatField('Dilution of Precision', null=True)
    time = models.TimeField('Time')
    date = models.DateField('Date')
    datetime = models.DateTimeField('Date and Time', primary_key=True)
    lat = models.DecimalField('Latitude (Deg, Dec. Min. N)', max_digits=8, decimal_places=5)
    lng = models.DecimalField('Longitude (Deg, Dec. Min. W)', max_digits=9, decimal_places=5)
    acoustic_range_cm = models.DecimalField('Acoustic Range (cm)', max_digits=5, decimal_places=2)
    optical_range_cm = models.DecimalField('Optical Range (cm)', max_digits=10, decimal_places=5)
    top_light = models.IntegerField('Irradiance)')
    bottom_light = models.IntegerField('Reflectance)')
    wind_m_s = models.DecimalField('Wind Speed (m/s)', max_digits=5, decimal_places=2)
    temp_C = models.DecimalField('Temperature (C)', max_digits=4, decimal_places=1, null=True)
    voltage = models.FloatField('Battery Voltage (V)')

    def __unicode__(self):
        return str(self.date) + ', ' + str(self.time)
