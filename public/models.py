from django.db import models

class B1Ablation(models.Model):
    '''Ablation measurement at GASS B1; identical to B2Ablation model.'''
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
    '''Ablation measurement at GASS B2; identical to B1Ablation model.'''
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

class AblationMeasurement(models.Model):
    '''An ablation measurement from before or during 2010'''
    id = models.IntegerField()
    # This is not the primary key, as it isn't as useful as datetime;
    #   it is, however, necessary for iterating through records
    site = models.TextField('Site Name')
    name = models.CharField('Original Filename', max_length=50)
    date = models.DateField('Date')
    time = models.TimeField('Time')
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
    jtime = models.FloatField('Julian Time')
    ntrans = models.IntegerField()
    temp_C = models.IntegerField('Temperature (C)')
    wind_m_s = models.FloatField('Wind Speed (m/s)')
    range_cm = models.IntegerField('Range (cm)')
    top_uW_cm2 = models.FloatField('Irradiance (uW/[cm-cm])')
    bottom_uW_cm2 = models.FloatField('Reflectance (uW/[cm-cm])')
    voltage = models.FloatField('Battery Voltage (V)')
    latitude = models.FloatField('Latitude (decimal degrees)')
    longitude = models.FloatField('Longitude (decimal degrees)')
    lat_deg = models.IntegerField('Latitude (degrees)')
    lat_min = models.FloatField('Latitude (minutes)')
    long_deg = models.IntegerField('Longitude (degrees)')
    long_min = models.FloatField('Longitude (minutes)')

    def __unicode__(self):
        return self.site + ', ' + str(self.date) + ', ' + str(self.time)
