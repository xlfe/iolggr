import Ember from 'ember';
//import d3 from 'd3';
/* global d3 */
/* global moment */

var tz = "Australia/Sydney",
    datetime_local = 'dddd, MMMM Do YYYY, h:mm:ss a';


var chart_types = {
    temp: {
        yAccessor: function(d){
            return +d.temp/100;
        },
        yFormat: function(d){
            return d+"°C";
        }
    },
    pressure: {
        yAccessor: function(d){
            return +d.pressure/1000;
        },
        yFormat: function(d){
            return (Math.round(d*100)/100)+"kPa";
        }
    },
    delay: {
        yAccessor: function(d){
            return +d.delay;
        },
        yFormat: function(d){
            return d+" ms";
        }
    },
    rssi: {
        yAccessor: function(d){
            return d.rssi;
        },
        yFormat: function(d){
            return d;
        }
    }
}




export default Ember.Component.extend({
    height: 180,
    width: 960,
    margins: {
        top: 20,
        bottom: 50,
        left: 100,
        right: 20
    },
    _get: function(nm) {
        var vars = this.get('vars');

        if (nm in vars){
            return vars[nm];
        }

        return this.get(nm);
    },
    vars: function(){
        var ct = this.get('chart-type');
        return chart_types[ct];
    }.property('chart-type'),
    xFormat: function(d){
        return moment(d).fromNow();
    },
    didInsertElement: function () {
        var data = this.get('data'),
            _this = this,
            d = d3.select(this.$('#chart')[0]);

        var margin = this.get('margins'),
            width = this.get('width') - margin.left - margin.right,
            height = this.get('height') - margin.top - margin.bottom;

        var x = d3.time.scale()
            .range([0, width])
            .nice(d3.time.hour);

        var y = d3.scale.linear()
            .range([height, 0])
            .nice();

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom")
            .ticks(4)
            .tickFormat(_this._get("xFormat"));

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left")
            .ticks(4).tickFormat(_this._get("yFormat"));

        var line = d3.svg.line()
            .x(function (d) {
                return x(d.dt);
            })
            .y(function (d) {
                d = _this._get('yAccessor')(d);
                return y(d);
            });

        var svg = d.append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        data.forEach(function (d) {
            d.dt = moment.utc(d.dt).tz(tz);

        });

        x.domain(d3.extent(data, function (d) {
            return d.dt;
        }));
        y.domain(d3.extent(data, function (d) {
            return _this._get('yAccessor')(d);
        }));

        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);

        svg.append("g")
            .attr("class", "y axis")
            .call(yAxis);

        svg.append("path")
            .datum(data)
            .attr("class", "line")
            .attr("d", line);

    }
});