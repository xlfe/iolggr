import DS from 'ember-data';
/* global moment */

var tz = "Australia/Sydney";

export default DS.Transform.extend({
    deserialize: function(serialized) {
        var dt = moment.utc(serialized).tz(tz).toDate();
        //console.log(serialized,dt);
        return dt;
    },
    serialize: function(deserialized) {
        return moment(deserialized).valueOf();
    }
});
