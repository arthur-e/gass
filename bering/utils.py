import datetime

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

