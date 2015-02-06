import Em from 'ember';

export default Em.Route.extend({
    model: function (params) {

        if (Em.isNone(params.devices)) {
            return null;
        }
        var store = this.get('store');

        return new Em.RSVP.all(
            params.devices.split(',').map(function (device) {
                return store.find('device', {id: device, rel: 0})
            })
        ).then(function (devices) {

                console.log(devices);

                return Em.Object.create({
                    _devices: devices.map(function(d){
                        return d.get('firstObject');
                    })
                })

            }
        );
    }
});
