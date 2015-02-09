import collections
import logging
from google.appengine.ext import ndb
from google.appengine.ext import deferred
from datetime import timedelta
import random
import json


format_timestamp = lambda x:x.replace(microsecond=0).isoformat()



class iot_event_roll(ndb.Model):

    start = ndb.DateTimeProperty(required=True)
    end = ndb.ComputedProperty(lambda x: x.start + x.period_length)

    #Actual data start and end dates
    d_start = ndb.DateTimeProperty(required=True)
    d_end= ndb.DateTimeProperty(required=True)

    updated = ndb.DateTimeProperty(auto_now=True)

    remote_addrs = ndb.StringProperty(repeated=True)
    mac = ndb.StringProperty(required=True)
    name = ndb.StringProperty()


    data = ndb.JsonProperty(compressed=False, indexed=False, default=[])
    offsets = ndb.JsonProperty(compressed=False, indexed=False, default={})

    def slice(self, _from, _to):

        logging.info('Slice requested for {} -> {}'.format(_from,_to))


        length = (self.period_length.total_seconds() / self.chunk_length.total_seconds())


        assert _from >= 0
        assert _to   < length
        assert _from <= _to

        start = 0
        start_dt = self.d_start
        if _from > 0:
            while _from not in self.offsets and _from > 0:
                _from -= 1

            try:
                start,start_dt = self.offsets[_from]
            except KeyError:
                start = 0
                start_dt = self.d_start
                _from = 0

        end = len(self.data)
        end_dt = self.d_end
        if _to < (length - 1):
            _to += 1
            while _to not in self.offsets and _to < (length - 1):
                _to += 1

            try:
                end,end_dt = self.offsets[_to]
            except KeyError:
                end = len(self.data)
                end_dt = self.d_end
                _to = (length - 1)

        logging.info('Found offsets for {} -> {}'.format(_from,_to))
        logging.info('Slice is {}:{}'.format(start,end))
        slice = self.data[start:end]
        zero = list(slice[0])
        zero[0] = 0
        slice[0] = tuple(zero)
        return start_dt,end_dt,slice

    def dt_to_chunk(self,dt):
        raise NotImplementedError()

    @classmethod
    def dt_to_period(cls,dt):
        raise NotImplementedError()

    @classmethod
    def get_or_create(cls,mac,start):
        o = cls.query().filter(cls.mac== mac, cls.start == start).get()

        if o is None:
            o = cls(mac=mac, start=start)
            o.d_end = start
            o.d_start = start

        return o

    def append(self,events):
        self.d_end = iot_event_roll._append(
            _start=self.start,
            _end=self.end,
            _d_end=self.d_end,
            events=events,
            data=self.data,
            offsets=self.offsets,
            dt_to_chunk=self.dt_to_chunk,
            stored_params=self.stored_params
        )

        if len(events)>0:
            e = events[-1]
            self.name = e.name
            if e.remote_addr not in self.remote_addrs:
                self.remote_addrs.append(e.remote_addr)

    @staticmethod
    def _append(_start, _end,_d_end,events,data,offsets,dt_to_chunk,stored_params,enforce_end=True):
        micro = timedelta()
        all_seconds=[]
        d_end = _d_end

        for e in events:

            assert e.timestamp >= _start, '{} > {}'.format(e.timestamp, _start)
            assert e.timestamp >= d_end, '{} > {}'.format(e.timestamp,d_end)

            if enforce_end:
                assert e.timestamp < _end, '{} < {}'.format(e.timestamp,_end)

            prev_chunk = dt_to_chunk(d_end)
            diff = (e.timestamp - d_end)

            micro += timedelta(microseconds=diff.microseconds)

            diff_seconds = int(diff.total_seconds())

            if micro.seconds > 0:
                diff_seconds += micro.seconds
                micro -= timedelta(seconds=micro.seconds)

            o = [diff_seconds] + [int(e.params[k]) for k in stored_params.split(',')]

            this_chunk = dt_to_chunk(e.timestamp)
            if prev_chunk != this_chunk:
                logging.info('CHUNK {} -> {} after {} obs'.format(prev_chunk,this_chunk,len(data)))
                offsets[this_chunk] = (len(data),format_timestamp(e.timestamp))

            d_end = e.timestamp
            data.append(o)
            all_seconds.append(diff_seconds)

        calc_seconds = int((d_end - _d_end).total_seconds())
        summed_seconds = sum(all_seconds)
        if calc_seconds != summed_seconds:
            new_end = (_d_end + timedelta(seconds=summed_seconds))
            raise FloatingPointError('New end date of {} does not match last obs {}'.format(new_end,d_end))

        return d_end




class iot_week(iot_event_roll):

    #Test
    period_length=timedelta(hours=6)
    chunk_length=timedelta(hours=1)

    #Weekly
    # period_length=timedelta(days=7)
    # chunk_length=timedelta(days=1)
    stored_params = 'temp,pressure,rssi,w_delay,delay'

    @classmethod
    def dt_to_period(cls,dt):
        # return dt.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=dt.isoweekday() - 1)
        h = dt.hour
        return dt.replace(hour=h-h%6, minute=0, second=0, microsecond=0)


    def dt_to_chunk(self,dt):
        return int((dt - self.start).total_seconds()/3600)
        # return (dt - self.start).days



class iot_exception(ndb.Model):

    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    mac = ndb.StringProperty()
    exception = ndb.StringProperty(choices=['CONNECTION','WIFI'])
    params = ndb.JsonProperty(indexed=False)


class iot_event(ndb.Model):
    """
        Params should include:

        Store these for device identification:
            MAC = 1340c89be4c1
            remote_addr

        Dont store these:
            AP-bssid = fc:75:16:53:ef:dc
            w_att = 1
            c_att = 1
            AP-authmode = 2
            AP-mode = 1
            AP-channel = 6

        Keep this in iot_event:
            name = Office

        Keep these in params:
            pressure = 94799
            temp = 2625
            AP-rssi = -82
            delay = 7079
            w_delay = 6793
        """

    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    mac = ndb.StringProperty()
    remote_addr = ndb.StringProperty()
    name = ndb.StringProperty()
    params = ndb.JsonProperty(indexed=False)

def rollup_events(batch_size=1000):
    """Roll-up individual events into a single iot_week object"""

    events = iot_event.query().order(iot_event.mac, iot_event.timestamp).fetch(batch_size)

    if len(events) == 0:
        return
    elif len(events) == 1000:
        deferred.defer(rollup_events,_queue='rollup')

    mac_weeks = collections.defaultdict(lambda: collections.defaultdict(list))

    for e in events:
        mac_weeks[e.mac][iot_week.dt_to_period(e.timestamp)].append(e)

    for mac,weeks in mac_weeks.iteritems():

        for week,events in weeks.iteritems():

            rollup = iot_week.get_or_create(mac=mac,start=week)
            rollup.append(events)

            logging.info('{} events for {} added into rollup({}) with {} total events'.format(len(events),mac,week,len(rollup.data)))
            # rollup.put()
            # ndb.delete_multi([e.key for e in events])





