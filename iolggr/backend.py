





import webapp2
import logging
import json
from json.encoder import INFINITY,encode_basestring,encode_basestring_ascii,c_make_encoder,_make_iterencode
from google.appengine.ext import ndb
from models import iot_event
from datetime import date,datetime,time

class NDBEncoder(json.JSONEncoder):
    """JSON encoding for NDB models and properties"""

    #Override floattr repr
    def iterencode(self, o, _one_shot=False):
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = encode_basestring_ascii
        else:
            _encoder = encode_basestring
        if self.encoding != 'utf-8':
            def _encoder(o, _orig_encoder=_encoder, _encoding=self.encoding):
                if isinstance(o, str):
                    o = o.decode(_encoding)
                return _orig_encoder(o)

        def floatstr(o, allow_nan=self.allow_nan,
                     _repr=None, _inf=INFINITY, _neginf=-INFINITY):
            # Check for specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.

            if o != o:
                text = 'NaN'
            elif o == _inf:
                text = 'Infinity'
            elif o == _neginf:
                text = '-Infinity'
            else:
                return format(o,'.2f')

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text


        # if (_one_shot and c_make_encoder is not None
        #         and self.indent is None and not self.sort_keys):
        #     _iterencode = c_make_encoder(
        #         markers, self.default, _encoder, self.indent,
        #         self.key_separator, self.item_separator, self.sort_keys,
        #         self.skipkeys, self.allow_nan)
        # else:
        _iterencode = _make_iterencode(
            markers, self.default, _encoder, self.indent, floatstr,
            self.key_separator, self.item_separator, self.sort_keys,
            self.skipkeys, _one_shot)
        return _iterencode(o, 0)


    def _decode_key(self, key):
        # model_class = ndb.Model._kind_map.get(key.kind())
        return key.urlsafe()

    def default(self, obj):
        if isinstance(obj, ndb.Model):
            obj_dict = obj.to_dict()

            # Filter the properties that will be returned to user
            obj_dict = dict((k,v) for k,v in obj_dict.iteritems())

            # Each BlobKeyProperty is represented as a dict of upload_url/download_url
            # for (name, prop) in obj._properties.iteritems():
            #     if isinstance(prop, ndb.FloatProperty):
            #         obj_dict[name] = '{:.2f}'.format(obj_dict[name])

            # Translate the property names
            if obj.key is not None:
                obj_dict['id'] = self._decode_key(obj.key)

            return obj_dict

        elif isinstance(obj, datetime) or isinstance(obj, date) or isinstance(obj, time):
            return obj.isoformat()[:-7]

        elif isinstance(obj, ndb.Key):
            return self._decode_key(obj)

        elif isinstance(obj, ndb.BlobKey):
            return str(obj)
        elif isinstance(obj, ndb.GeoPt):
            return str(obj)

        else:
            return super(NDBEncoder,self).default(self, obj)


class device_handler(webapp2.RequestHandler):

    def get_response(self, status, content):
        """Returns an HTTP status message with JSON-encoded content (and appropriate HTTP response headers)"""

        # Create the JSON-encoded response
        try:
            response = webapp2.Response(json.dumps(content, cls=NDBEncoder))
        except:
            logging.info(content)
            raise

        response.status = status

        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Content-Type'] = 'application/json'

        return response


    def get(self,dev_id):

        _results = iot_event.query().filter(iot_event.mac == dev_id).order(-iot_event.timestamp).fetch(1000)

        if _results == []:
            return self.get_response(404,{})

        results = []
        for r in _results:
            p = r.params.copy()
            for d in ['AP-mode','AP-bssid','AP-authmode','AP-channel','w_att','c_att','delay','w_delay','name']:
                del p[d]
            for k,v in p.iteritems():
                p[k] = int(v)
            p['rssi'] = p['AP-rssi']
            del p['AP-rssi']
            p['dt'] = r.timestamp
            results.append(p)



        device = {
            'device': {
                'name': _results[0].params['name'],
                'id':dev_id,
                'results': results
            }
        }

        return self.get_response(200,device)





api = webapp2.WSGIApplication([
    ('/api/devices/([^/]+)', device_handler),
    ], debug=True)
