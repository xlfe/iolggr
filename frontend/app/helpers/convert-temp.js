import Em from 'ember';

export default Em.Handlebars.makeBoundHelper(function(temp) {
    return (+temp / 100).toFixed(2) + "°C";
});

