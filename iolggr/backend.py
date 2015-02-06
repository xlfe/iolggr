



#
#
import webapp2
import logging
import json
from json.encoder import INFINITY,encode_basestring,encode_basestring_ascii,c_make_encoder,_make_iterencode
from google.appengine.ext import ndb
from models import iot_event,iot_week,format_timestamp
from datetime import date,datetime,time,timedelta

to_dt = lambda x:datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')

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

class json_response(webapp2.RequestHandler):

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



class ip_handler(json_response):

    def get(self):
        my_remote_addr = self.request.remote_addr

        recent = iot_event.query(projection=['mac','name'], distinct=True).filter(iot_event.remote_addr == my_remote_addr).fetch(1000)
        logging.info('{} results fetched from projection query on iot_event'.format(len(recent)))

        older = iot_week.query(projection=['mac','name'], distinct=True).filter(iot_week.remote_addrs == my_remote_addr).fetch(1000)
        logging.info('{} older results fetched from projection query on iot_week'.format(len(older)))

        macs = {}
        for r in recent + older:
            macs[r.mac]=r.name

        return self.get_response(200,{
            'iplist': {
                'id': 'me',
                'results': macs
            }
        })

class device(object):

    def __init__(self,dev_id):
        self.dev_id = dev_id
        if dev_id =='9be4c11340c8': self.dev_id = '1340c89be4c1'

        if iot_event.query(iot_event.mac == dev_id).fetch(1,keys_only=True) is None:
            if iot_week.query(iot_week.mac == dev_id).fetch(1,keys_only=True) is None:
                raise AttributeError('No device with MAC {} found'.format(dev_id))

    def _week(self,dt):
        _dt = iot_week.dt_to_week(dt)
        return iot_week.query(iot_week.mac == self.dev_id).filter(iot_week.start == _dt).get()


    def _weeks(self,start,end):

        assert end > start

        _start = iot_week.dt_to_week(start)
        weeks = []

        while _start < end:
            weeks.append(_start)
            _start += timedelta(days=7)

        weeks = iot_week.query(iot_week.mac == self.dev_id).filter(iot_week.start.IN(weeks)).order(iot_week.start).fetch(10)
        logging.info('{} weeks retrieved with start {} and end {}'.format(len(weeks),start.isoformat(),end.isoformat()))
        for week in weeks:
            logging.info('{} - {} with {} obs'.format(week.start,week.end,len(week.data)))

        #Remove observations outside the start/end pair...
        if False:
            o_count =0
            for week in weeks:
                outliers = []
                for k in week.data:
                    _k = to_dt(k)
                    if _k > end or _k < start:
                        outliers.append(k)
                for o in outliers:
                    o_count+=1
                    del week.data[o]

            logging.info('{} outliers removed'.format(o_count))
        return weeks

    def week(self,dt):
        week = self._week(dt)
        if week is not None:
            device.clean_week(self.week(dt))
        return week

    def weeks(self,start,end):
        weeks = self._weeks(start=start,end=end)
        for week in weeks:
            device.clean_week(week)
        return weeks

    @property
    def name(self):
        recent = iot_event.query(projection=['name'], distinct=True).filter(iot_event.mac == self.dev_id).get()
        try:
            return recent.name
        except AttributeError:
            older = iot_week.query(projection=['name'], distinct=True).filter(iot_week.mac == self.dev_id).get()
            return older.name

    def prefetch_recent(self):
        setattr(self,'__recent',iot_event.query(iot_event.mac==self.dev_id).fetch_async(1000))

    def resolve_recent(self):
        __recent = getattr(self,'__recent',None)
        assert __recent is not None
        result = __recent.get_result()
        setattr(self,'__recent',None)
        return result

    def most_recent_observation(self):
        """
            Get the most recent observation for the device
        """
        e = iot_event.query(iot_event.mac == self.dev_id).order(-iot_event.timestamp).get()

        try:
            return e.name,{
                format_timestamp(e.timestamp):self.clean_observation(e.params)
            }

        except AttributeError:
            w = iot_week.query(iot_week.mac == self.dev_id).order(-iot_week.end).get()

            assert w is not None
            assert len(w.data) > 0

            latest = sorted(w.data)[-1]
            return w.name,{
                latest:self.clean_observation(w.data[latest])
            }

    @staticmethod
    def clean_week(week):
        for k in week.data:
            week.data[k] = device.clean_observation(week.data[k])

    @staticmethod
    def clean_observation(result):
        return {k:result[k] for k in ['temp','pressure']}


class device_single(json_response):
    def get(self,dev_id):
        """Get 1 week worth of data plus most recent.

        rel: relative to utc.now() - ie 0 is now, -1 is last week, etc

        start, end: get data between

        """
        try:
            dev = device(dev_id=dev_id)
        except AttributeError:
            return self.get_response(404,{})

        name,result = dev.most_recent_observation()

        return self.get_response(200, {
            'device': {
                'id': dev_id,
                'name':name,
                'obs': result
            }
        })


class device_query(json_response):

    def get(self):
        dev_id = self.request.get('id',None)

        try:
            dev = device(dev_id=dev_id)
        except AttributeError:
            return self.get_response(404,{})

        rel = self.request.get('rel',None)

        if rel is not None:
            try:
                rel = int(rel)
            except ValueError:
                return self.get_response(500, {})

            start = datetime.now() - timedelta(days=(rel+1)*7)
            end   = datetime.now() - timedelta(days=(rel+0)*7)

        else:
            start = self.request.get('start', None)
            end = self.request.get('end', None)

            if end is None:
                end = datetime.now()
            else:
                end = to_dt(end)

            if start is not None:
                start = to_dt(start)


        assert start < datetime.now()

        prefetch = end > datetime.now() - timedelta(hours=3)
        if prefetch:
            dev.prefetch_recent()
            logging.info('Pre-fetching most recent observations')

        weeks = dev.weeks(start=start,end=end)
        result = {}

        if len(weeks) == 0 and prefetch is False:
            #No historical data, recent data not requested...
            return self.get_response(204, {})

        if len(weeks) > 0:
            name = weeks[-1].name

            for week in weeks:
                result.update(week.data)

        if prefetch:
            recent = dev.resolve_recent()
            for r in recent:
                result[format_timestamp(r.timestamp)] = device.clean_observation(r.params)
            if len(recent)>0:
                name = recent[-1].name
            logging.info('{} recent results appended'.format(len(recent)))

        return self.get_response(200,{
            "Device": [
                {
                    'id': dev_id,
                    'name':name,
                    'obs': result
                }
            ]
        })


api = webapp2.WSGIApplication([
    ('/api/iplists/me', ip_handler),
    ('/api/devices/([^/]+)', device_single),
    ('/api/devices', device_query),
    ], debug=True)




















