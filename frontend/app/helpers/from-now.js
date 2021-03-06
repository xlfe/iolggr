import Em from 'ember';
/* global moment */

var tz = "Australia/Sydney";
export default Em.Handlebars.makeBoundHelper(function(date) {
    return moment.utc(date).tz(tz).fromNow();
});
