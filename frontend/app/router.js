import Ember from 'ember';
import config from './config/environment';

var Router = Ember.Router.extend({
  location: config.locationType
});

Router.map(function() {
    this.resource('charts'),
    this.resource('chart', {path: '/chart/:id'}),
    this.resource('devices'),
    this.resource('device', {path: '/device/:id'});
});

export default Router;
