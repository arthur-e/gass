import csv, ipdb
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.encoding import smart_str
from django.core.serializers.json import DateTimeAwareJSONEncoder
from piston.emitters import Emitter

class IdentityEmitter(Emitter):
    '''
    The standard Django Piston emitter does unnecessary computations when an
    emitter is searching for the raw data from its associated handler.
    '''
    def construct(self):
        return self.data


class JSONEmitter(Emitter):
    '''
    JSON emitter, understands timestamps, wraps result set in object literal
    for ExtJS compatibility.
    '''
    def render(self, request):
        cb = request.GET.get('callback')
        package = self.construct()
        ext_dict = {
            'data': package,
            'success': True
        }

        # Try to add a 'results' param with the number of records
        try: ext_dict['results'] = len(package)
        except TypeError: pass

        if request.GET.get('sid'):
            ext_dict['sid'] = request.GET.get('sid')

        seria = simplejson.dumps(ext_dict, cls=DateTimeAwareJSONEncoder, ensure_ascii=False, indent=4)

        # Callback
        if cb:
            return '%s(%s)' % (cb, seria)

        return seria


class GeoJSONEmitter(IdentityEmitter):
    '''
    GeoJSON emitter for FeatureCollections.
    '''
    def render(self, request):
        cb = request.GET.get('callback')
        geojson_dict = {
            'type': 'FeatureCollection',
            'features': self.construct()
        }
        seria = simplejson.dumps(geojson_dict, cls=DateTimeAwareJSONEncoder, ensure_ascii=False, separators=(',',':'), indent=0) 
        # Remove separators argument set indent to 4 for "pretty printing"

        # Callback
        if cb:
            return '%s(%s)' % (cb, seria)

        return seria


class CSVEmitter(Emitter):
    '''
    Emitter for exporting to CSV (excel dialect).
    '''
    def get_keys(self, input_dict):
        keys = []
        for item in input_dict.items():
            if isinstance(item[1], dict):
                keys.extend(self.get_keys(item[1]))
            else:
                keys.append(item[0])
        return keys
    

    def get_values(self, input_dict):
        for item in input_dict.items():
            if isinstance(item[1], dict):
                input_dict.update(self.get_values(input_dict.pop(item[0])))
            else:
                input_dict[item[0]] = smart_str(item[1])
        return input_dict

    
    def render(self, request):
        response = HttpResponse(mimetype='text/csv')
        content = self.construct()
        keys = self.get_keys(content[0])
        
        writer = csv.DictWriter(response, keys, dialect='excel')
        headers = dict((n,n) for n in keys)
        writer.writerow(headers)
        for row in content:
            writer.writerow(self.get_values(row))
        
        return response

    
Emitter.register('json', JSONEmitter, 'application/json; charset=utf-8')
Emitter.register('csv', CSVEmitter, 'text/csv; charset=utf-8')
Emitter.register('geojson', GeoJSONEmitter, 'application/json; charset=utf-8')
