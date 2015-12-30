import collections
import logging
from google.appengine.ext import ndb
from google.appengine.ext import deferred
from datetime import timedelta,datetime
import random
import json


format_timestamp = lambda x:x.replace(microsecond=0).isoformat()
to_dt = lambda x:datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')


class iot_event_roll(ndb.Model):

    start = ndb.DateTimeProperty(required=True)
    end = ndb.ComputedProperty(lambda x: x.start + x.period_length)

    #Actual data start and end dates
    d_end= ndb.DateTimeProperty(required=True)

    updated = ndb.DateTimeProperty(auto_now=True)

    remote_addrs = ndb.StringProperty(repeated=True)
    mac = ndb.StringProperty(required=True)
    name = ndb.StringProperty()


    data = ndb.JsonProperty(compressed=False, indexed=False)
    offsets = ndb.JsonProperty(compressed=False, indexed=False)

    @property
    def d_start(self):
        if len(self.data) == 0:
            return self.start
        return self.start + timedelta(seconds=self.data[0][0])

    @property
    def num_periods(self):
        return (self.period_length.total_seconds() / self.chunk_length.total_seconds())

    def slice(self, _from, _to):

        _s = lambda x: str(int(x))
        logging.info('Slice requested for {} -> {}'.format(_s(_from),_s(_to)))

        logging.info(self.offsets)
        length = self.num_periods

        assert _from >= 0
        assert _to   <  length
        assert _from <= _to

        start = 0
        start_dt = self.d_start
        if _from > 0:
            while _s(_from) not in self.offsets and _from > 0:
                _from -= 1

            try:
                start,start_dt = self.offsets[_s(_from)]
                start_dt = to_dt(start_dt)
            except KeyError:
                start = 0
                start_dt = self.d_start
                _from = 0

        end = len(self.data)
        end_dt = self.d_end
        if _to < (length - 1):
            _to += 1
            while _s(_to) not in self.offsets and _s(_to) < (length - 1):
                _to += 1

            try:
                end,end_dt = self.offsets[_s(_to)]
                end_dt = to_dt(end_dt)
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
    def gen_id(cls,mac,start):
        return '{}#{}'.format(mac.lower(),format_timestamp(start))

    @classmethod
    def get(cls, mac, start):
        assert start.microsecond == 0
        return ndb.Key(cls,cls.gen_id(mac,start)).get()


    @classmethod
    def get_or_create(cls, mac, start):

        o = cls.get(mac,start)

        if o is None:
            o = cls(id=cls.gen_id(mac,start))
            o.mac = mac
            o.start = start
            o.d_end = start
            o.data = []
            o.offsets = {}

        return o

    def append(self,events):

        #propogate the most-recent event name to the rollup name
        if len(events)>0:
            self.name = events[-1].name

        #add all remote_addrs from the events to the rollup remote addrs
        for e in events:
            if e.remote_addr not in self.remote_addrs:
                self.remote_addrs.append(e.remote_addr)

        #rollup the actual events
        self.d_end = iot_event_roll._append(
            _start=self.start,
            _end=self.end,
            _d_end=self.d_end,
            events=events,
            _data=self.data,
            offsets=self.offsets,
            dt_to_chunk=self.dt_to_chunk,
            stored_params=self.stored_params
        )

    @staticmethod
    def _append(_start, _end, _d_end, events, _data, offsets, dt_to_chunk, stored_params):
        """

        :param _start:          Rollup period start
        :param _end:            Rollup period end
        :param _d_end:          Existing end point for this rollup
        :param events:          List of events to rollup
        :param _data:           Data list to rollup into
        :param offsets:         Dictionary to store chunk offsets
        :param dt_to_chunk:     Function that calculates the chunk
        :param stored_params:   List indicating params to rollup from each event
        :return:                New d_end for the rollup
        """

        #Should not have microseconds
        assert _d_end.microsecond == 0

        #dont overwrite the existing endpoint
        d_end = _d_end

        #Store the newly rolled up events before adding them
        data = []

        for e in events:

            #Make sure each event actually belongs in this rollup
            assert e.timestamp < _end, 'Assertion Failed: {} < {}'.format(e.timestamp, _end)
            assert e.timestamp >= _start, 'Assertion Failed: {} < {}'.format(e.timestamp, _start)

            #Assert that we've been given the events in order
            assert e.timestamp >= d_end, 'Assertion Failed: {} >= {}'.format(e.timestamp, d_end)

            #We want precesion to be no greater than 1 second
            ts = e.timestamp.replace(microsecond=0)

            #Previous chunk is based on the previous data end point
            prev_chunk = dt_to_chunk(d_end)

            #Seconds difference between previous pt and the new pt
            diff = (ts - d_end).total_seconds()

            #Actual rollup data: diff_in_seconds, param_1, ...
            o = [int(diff)] + [int(e.params[k]) for k in stored_params.split(',')]

            #Current chunk
            this_chunk = dt_to_chunk(ts)

            #If we've just moved into the next chunk, store the chunk boundary for later use
            if prev_chunk != this_chunk:
                logging.info('CHUNK {} -> {} after {} obs'.format(prev_chunk,this_chunk,len(data)+len(_data)))

                #chunk boundaries are (n_previous_observations, timestamp)
                offsets[this_chunk] = (len(_data) + len(data),format_timestamp(ts))

            #update the data end_point and add the rollup
            d_end = ts
            data.append(o)

        #assert that the actual difference between the previous end point and the new endpoint matches the number
        #of seconds we've added
        append_diff = int((d_end - _d_end).total_seconds())
        all_seconds = sum(_[0] for _ in data)
        assert append_diff == all_seconds

        #add the new rollups to the actual rollup list and return the new data end point
        _data.extend(data)
        return d_end




class iot_week(iot_event_roll):

    #Test 6 hourly periods
    # period_length=timedelta(hours=6)
    # chunk_length=timedelta(hours=1)

    #Weekly
    period_length=timedelta(days=7)
    chunk_length=timedelta(days=1)
    stored_params = 'temp,pressure,rssi,w_delay,delay'

    @classmethod
    def dt_to_period(cls,dt):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=dt.isoweekday() - 1)
        # h = dt.hour
        # return dt.replace(hour=h-h%6, minute=0, second=0, microsecond=0)


    def dt_to_chunk(self,dt):
        # return int((dt - self.start).total_seconds()/3600)
        assert dt >= self.start and dt <= self.end
        return (dt - self.start).days



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

    _events = iot_event.query().order(iot_event.mac, iot_event.timestamp).fetch(batch_size)

    if len(_events) ==0:
        return

    mac_periods = collections.defaultdict(lambda: collections.defaultdict(list))

    for e in _events:
        mac_periods[e.mac][iot_week.dt_to_period(e.timestamp)].append(e)

    for mac, periods in mac_periods.iteritems():

        for period, events in periods.iteritems():

            rollup = iot_week.get_or_create(mac=mac, start=period)

            rollup.append(events)

            rollup.put()
            logging.info('{} events for {} added into {} with {} total events'.format(len(events), rollup.key, period,
                                                                                      len(rollup.data)))
            logging.info('Event extent is {} -> {}'.format(events[0].timestamp, events[-1].timestamp))
            logging.info('Data extent is {} -> {}'.format(rollup.d_start, rollup.d_end))
            ndb.delete_multi([e.key for e in events])

    if len(_events) == 1000:
        deferred.defer(rollup_events, _queue='rollup')


