from django.db import models

class Albation(models.Model):
    '''
    Ablation measurement from the 2012 campaign.
    '''
    STATIONS = (
        ('t01', 'T01')
        ('b01', 'B01')
        ('b02', 'B02')
        ('b03', 'B03')
        ('b04', 'B04')
        ('b06', 'B06')
    )
    site = models.CharField(max_length=255, choices=STATIONS)
    sats = models.IntegerField(verbose_name='satellites', help_text='Number of satellites')
    hdop = models.FloatField(help_text='Horizontal dilution of precision (HDOP)', null=True)
    time = models.TimeField()
    date = models.DateField()
    datetime = models.DateTimeField(help_text='Date and time of measurement from GPS')
    lat = models.DecimalField(help_text='Latitude (Deg, Dec. Min. N)', max_digits=8, decimal_places=5)
    lng = models.DecimalField(help_text='Longitude (Deg, Dec. Min. W)', max_digits=9, decimal_places=5)
    range_cm = models.DecimalField(verbose_name='acoustic range (cm)', 'Acoustic Range (cm)', max_digits=5, decimal_places=2)
    top = models.IntegerField(verbose_name='irradiance')
    bottom = models.IntegerField(verbose_name='reflectance')
    wind_spd = models.DecimalField(verbose_name='wind speed (m/s)', max_digits=5, decimal_places=2)
    temp_C = models.DecimalField(verbose_name='temperature (C)', max_digits=4, decimal_places=1, null=True)
    voltage = models.FloatField(verbose_name='battery voltage (V)')

    def __unicode__(self):
        return str(self.date) + ', ' + str(self.time)


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
