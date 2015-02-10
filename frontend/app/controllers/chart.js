import Em from 'ember';

export default Em.ObjectController.extend({
    actions: {
        remove: function (dev) {
            var d = this.get('_devices');

            if (d.length <= 1) {
                alert("You must have at least one device on the chart");
                return;
            }
            d.removeObject(dev);

            var devices = this.get('devices').split(',');
            devices.removeObject(dev.get('id'));
            this.set('devices', devices.join(','));
        },
        refresh: function () {
            this.dev_observer();
        }
    },
    model: {},
    colours: {},
    c_i: 1,
    queryParams: ['devices'],

    dev_observer: function () {

        var store = this.get('store'),
            _this = this,
            devices = this.get('devices');

        if (Em.isNone(devices)) {
            return;
        }

        new Em.RSVP.all(devices.split(',').map(function (device) {
                return store.find('device', {id: device, rel: 0});
            })
        ).then(function (devices) {
                _this.set('_devices',
                    devices.map(function (d) {
                        var dev = d.get('firstObject'),
                            i = _this.get('c_i'),
                            colours = _this.get('colours');

                        if (dev.get('id') in colours) {
                            dev.set('colour', colours[dev.get('id')]);
                        }else {
                            dev.set('colour', i);
                            colours[dev.get('id')] = i;
                            _this.incrementProperty('c_i');
                            _this.set('colours',colours);
                        }

                        return dev;
                    })
                );
            }
        );
    }.observes('devices')
});
