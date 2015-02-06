import Ember from 'ember';
import config from './config/environment';

var Router = Ember.Router.extend({
  location: config.locationType
});

Router.map(function() {
    this.resource('charts',function() {
        this.resource('chart')
    }),
    this.resource('devices', function() {
        this.resource('device',{path: '/:id'})
    });
});

export default Router;
