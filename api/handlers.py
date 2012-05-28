import re, datetime, time
from django.utils import simplejson as json
from django.db.models import Avg, Max, Min, StdDev
from django.db.models.fields import FieldDoesNotExist
from django.core.exceptions import FieldError
from django.core.cache import cache
from piston.handler import BaseHandler
from piston.utils import rc, require_mime, require_extended, validate
from bering.models import *

class APIHandler(BaseHandler):
    '''
    An abstract base class intended to be used in place of BaseHandler.
    '''
    def _respond_(self, template, message):
        '''
        A helper for the entirely too verbose process of writing rc messages.
        '''
        response = template
        response.write(message)
        return response


    def _dates_(self):
        '''
        A dates query.
        '''
        # Retrieve the cache
        cq = cache.get('%s_dates_query' % self.model._meta.object_name)

        # If a cached copy exists, return it
        if cq is not None:
            return cq

        query = self.model.objects.dates('datetime', 'day').only('datetime')

        dates_list = []
        for date in query:
            # Send the dates as a string to avoid client-side reformatting
            #   of Javascript date objects
            dates_list.append(date.strftime("%Y-%m-%d"))

        results = [{
            'asset': str(self.model.objects.latest().site),
            'dates': dates_list
        }]

        # Cache result for 59 minutes
        cache.set('%s_dates_query' % self.model._meta.object_name, results, 59*60)

        return results


    def _latest_(self, attrs):
        '''
        A latest data query.
        '''
        for param in ['span', 'step']:
            if param not in attrs.keys():
                return self._respond_(rc.BAD_REQUEST, " - Parameter '%s' was expected but not received" % param)

        span = attrs['span']
        step = attrs['step']

        try: span = int(span)
        except ValueError: return rc.BAD_REQUEST

        if step not in ['seconds', 'minutes', 'hours', 'days']:
            return self._respond_(rc.BAD_REQUEST, " - Parameter 'step' is expected to be one of the following: seconds, minutes, hours, or days")

        # Initialize result set containing only those records for named station/site by sid
        base = self.model.objects.filter(site__exact=attrs['sid'].lower())
        if len(base) == 0: return []

        # Retrieve the cache
        cq = cache.get('%s_last_%d_%s_query' % (self.model._meta.object_name, int(span), str(step)))

        # If a cached copy exists, return it
        if cq is not None:
            return cq

        # Set up a keyword argument to be passed to datetime.timedelta
        latest_dict = {step: int(span)}

        latest = base.latest().datetime
        from_last = latest - datetime.timedelta(**latest_dict)
        query = base.filter(datetime__range=(from_last, latest))

        # Cache result for 25 minutes (25 * 60 seconds)
        cache.set('%s_last_%d_%s_query' % (self.model._meta.object_name, int(span), str(step)), query, 25*60)

        return query


class AblationHandler(APIHandler):
    '''
    '''
    model = Ablation
    fields = model.get_base_field_names()
    exclude = ('id','pk') # Preserve default of excluding primary keys
    services = [
        'GetDates', 
        'GetLatest', 
        'GetObservation', 
    ]

    def _observation_(self, attrs):
        '''
        A query for time series observations.
        '''
        for param in ['begin', 'end']:
            if param not in attrs.keys():
                return self._respond_(rc.BAD_REQUEST, " - Parameter '%s' was expected but not received" % param)

        try:
            begin = datetime.datetime.strptime(attrs['begin'], '%Y-%m-%dT%H:%M:%S')
            end = datetime.datetime.strptime(attrs['end'], '%Y-%m-%dT%H:%M:%S')

        except ValueError:
            return self._respond_(rc.BAD_REQUEST, " - One or both of the parameters 'begin' and 'end' are not formatted correctly")

        query = self.model.objects.filter(timestamp__range=(begin, end)) # Initialize query

        # Filtering (multiple)
        if 'filter' in attrs:
            # Decode JSON request to Python obj
            try: obj = json.loads(attrs['filter']) 
            except ValueError: return rc.BAD_REQUEST
            qry = {} # Dictionary of filters to be passed in as keyword args

            # Check that there aren't too many filters
            if len(obj) > 5:
                return rc.THROTTLED

            # For each filter (dictionary), determine its type
            for fltr in obj:
                if fltr['type'] == 'numeric':
                    comp = '__' + fltr['comparison']
                    if fltr['comparison'] == 'eq':
                        comp = '__exact'

                    qry[fltr['field'] + comp] = fltr['value']

                elif fltr['type'] == 'string':
                    if fltr['field'] == 'geom':
                        qry[fltr['field'] + '__within'] = fltr['value']

                    else:
                        qry[fltr['field'] + '__icontains'] = fltr['value']

                elif fltr['type'] == 'list':
                    qry[fltr['field'] + '__in'] = fltr['value']

                else:
                    return rc.NOT_IMPLEMENTED

            query = query.filter(**qry)
 
        # Sorting (multiple)
        if 'sort' in attrs:
            # Decode JSON request to Python obj
            try: obj = json.loads(attrs['sort']) 
            except ValueError: return rc.BAD_REQUEST
            qry = [] # List of filters to be passed in as arguments

            # Check that there aren't too many sort fields
            if len(obj) > 3:
                return rc.THROTTLED

            # For each sorter (dictionary), determine the direction
            for sorter in obj:
                if sorter['direction'] != '':
                    if sorter['direction'].lower() == 'desc':
                        qry.append('-' + sorter['field'])

                    elif sorter['direction'].lower() == 'asc':
                        qry.append(sorter['field'])

                    else:
                        return rc.BAD_REQUEST

            query = query.order_by(*qry)

        # Paging
        if 'limit' in attrs.keys():
            if 'index' in attrs.keys(): index = int(attrs['index']) 
            else: index = 0 # Starting record index
            limit = index + int(attrs['limit']) # Ending record index
            return query[index:limit]

        # Finally, downselecting
        if 'fields' in attrs.keys():
            try: fields = json.loads(attrs['fields'])
            except ValueError: return rc.BAD_REQUEST

            results = []
            # Check that all requested field names are valid fields
            for field in fields:
                if field not in self.model.get_field_names():
                    return self._respond_(rc.BAD_REQUEST, " - An invalid field name was passed in the list of 'fields'")

            # Operate on each record dictionary, extrating only desired fields
            for each in query.values():
                data_dict = {}
                for field in fields:
                    data_dict[field] = each[field]

                results.append(data_dict)

            return results

        # If no downselecting, the result is the QuerySet
        return query


    def read(self, request):
        '''
        The handler for HTTP GET requests.
        '''
        attrs = self.flatten_dict(request.GET)

        # Basic rejection of requests without specification
        if 'request' not in attrs.keys():
            return self._respond_(rc.BAD_REQUEST, " - Parameter 'request' was expected but not received")

        # Require that an SID (site name or station ID) be passed
        if 'sid' not in attrs.keys():
            return self._respond_(rc.BAD_REQUEST, " - Parameter 'sid' was expected but not received")

        # Reject requests for unsupported services
        if attrs['request'] not in self.services:
            return rc.NOT_IMPLEMENTED

        # GetDates: Query available dates e.g. localhost/api/buoy/45023?request=GetDates
        if attrs['request'] == 'GetDates':
            return self._dates_()

        # GetLatest: Query latest data by hours e.g. localhost/api/buoy/45023?request=GetLatest&span=24&step=hour
        if attrs['request'] == 'GetLatest':
            return self._latest_(attrs)

        # GetObservation: Query time series observations e.g. localhost/api/buoy/45023?request=GetObservation&begin=2012-04-24T00:00:00&end=2012-04-24T00:06:00
        if attrs['request'] == 'GetObservation':
            return self._observation_(attrs)

