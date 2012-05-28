from django.utils import simplejson
from django.core.serializers.json import DateTimeAwareJSONEncoder
from piston.emitters import Emitter

class ExtJSONEmitter(Emitter):
    '''
    JSON emitter, understands timestamps, wraps result set in object literal
    for ExtJS compatibility.
    '''
    def render(self, request):
        cb = request.GET.get('callback')
        package = self.construct()
        ext_dict = {
            'success': True,
            'data': package,
        }
        try: ext_dict['results'] = len(package)
        except TypeError: pass
        seria = simplejson.dumps(ext_dict, cls=DateTimeAwareJSONEncoder, ensure_ascii=False, separators=(',',':'), indent=4) 
        # Remove separators argument set indent to 4 for "pretty printing"

        # Callback
        if cb:
            return '%s(%s)' % (cb, seria)

        return seria


class GeoJSONEmitter(Emitter):
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


Emitter.register('ext-json', ExtJSONEmitter, 'application/json; charset=utf-8')
Emitter.register('geojson', GeoJSONEmitter, 'application/json; charset=utf-8')
