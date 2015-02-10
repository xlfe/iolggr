



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

        if iot_event.query(iot_event.mac == dev_id).fetch(1,keys_only=True) is None:
            if iot_week.query(iot_week.mac == dev_id).fetch(1,keys_only=True) is None:
                raise AttributeError('No device with MAC {} found'.format(dev_id))

    def single(self,dt):
        start = iot_week.dt_to_period(dt)
        return iot_week.get(self.dev_id, start)

    def multiple(self,start,end):

        assert end > start

        _start = iot_week.dt_to_period(start)
        periods = []

        while _start < end:
            periods.append(ndb.Key(iot_week,iot_week.gen_id(self.dev_id,_start)))
            _start += iot_week.period_length

        results = filter(lambda x: x is not None, ndb.get_multi(periods))
        logging.info('{} periods retrieved between {} and end {}'.format(len(results),start.isoformat(),end.isoformat()))
        for r in results:
            logging.info('Period {} -> {} has {} obs'.format(r.start,r.end,len(r.data)))

        return results

    @property
    def name(self):
        recent = iot_event.query(projection=['name'], distinct=True).filter(iot_event.mac == self.dev_id).get()
        try:
            return recent.name
        except AttributeError:
            older = iot_week.query(projection=['name'], distinct=True).filter(iot_week.mac == self.dev_id).get()
            return older.name

    def prefetch_recent(self):
        setattr(self,'__recent',iot_event.query(iot_event.mac==self.dev_id).order(iot_event.timestamp).fetch_async(1000))

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

        if e is None:
            w = iot_week.query(iot_week.mac == self.dev_id).order(-iot_week.start).get()

            assert w is not None
            assert len(w.data) > 0

            obs = list(w.data[-1])
            obs[0] = 0
            name = w.name
            start = w.d_end
            key = w.stored_params
            data = tuple(obs)
        else:
            name = e.name
            start = format_timestamp(e.timestamp)
            key = iot_week.stored_params
            data = [0]+[int(e.params[k]) for k in iot_week.stored_params.split(',')]

        return {
            'id':self.dev_id,
            'name':name,
            'start': start,
            'keys': key,
            'obs':[data]
        }

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

        result = dev.most_recent_observation()
        return self.get_response(200, { 'device': result })

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

            start = datetime.now() - iot_week.period_length*(rel+1)
            end   = datetime.now() - iot_week.period_length*(rel+0)

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

        historical = dev.multiple(start=start,end=end)

        #No historical data and recent data not requested?
        if len(historical) == 0 and prefetch is False:
            return self.get_response(204, {})

        result = []
        start_dt = None
        end_dt = None

        if len(historical) > 0:

            #if we have rollup data, start date is start of that period
            #because the first observation always has seconds that indicate that...
            start_dt = historical[0].start

            for n,period in enumerate(historical):

                if n > 0:
                    #After the first period, every additional period we need to calculate the diff seconds
                    prev_p = historical[n-1]
                    assert period.d_start.microsecond == 0
                    assert prev_p.d_end.microsecond == 0

                    diff = int((period.d_start - prev_p.d_end).total_seconds())

                    zero = list(period.data[0])
                    zero[0] += diff
                    period.data[0] = tuple(zero)

                result.extend(period.data)
                end_dt = period.d_end
                name = period.name

        #Do we have recent results?
        if prefetch:
            recent = dev.resolve_recent()

            if len(recent) > 0:
                logging.info('{} recent obs found'.format(len(recent)))

                if len(historical) == 0:
                    logging.info('No historical data yet')
                    start_dt = recent[0].timestamp.replace(microsecond=0)
                    end_dt = start_dt

                data = []

                end_dt = iot_week._append(
                    _start=recent[0].timestamp.replace(microsecond=0),
                    _end=datetime.now(),
                    _d_end=end_dt,
                    events=recent,
                    _data=data,
                    offsets=None,
                    dt_to_chunk=lambda x:0,
                    stored_params=iot_week.stored_params,
                )

                name = recent[-1].name

                result.extend(data)
                logging.info('{} recent results appended'.format(len(data)))


        if True:
            s = start_dt
            for d in result:
                # logging.info('{} {} {}'.format(s,d[0],d))
                s += timedelta(seconds=d[0])

            logging.info('Data period appears to be {} -> {}'.format(start_dt,end_dt))
            logging.info('Calculated end date is {}'.format(s))
            assert end_dt == s

        return self.get_response(200,{
            "Device": [
                {
                    'id': dev_id,
                    'name': name,
                    'start':format_timestamp(start_dt),
                    'keys':iot_week.stored_params,
                    'obs': result
                }
            ]
        })




api = webapp2.WSGIApplication([
    ('/api/iplists/me', ip_handler),
    ('/api/devices/([^/]+)', device_single),
    ('/api/devices', device_query),
    ], debug=True)




















