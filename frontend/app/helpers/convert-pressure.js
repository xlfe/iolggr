import Em from 'ember';

export default Em.Handlebars.makeBoundHelper(function(pressure) {
    return (+pressure / 1000).toFixed(2) + 'kPa';
});

