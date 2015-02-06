import Ember from 'ember';
//import d3 from 'd3';
/* global d3 */
/* global moment */

var tz = "Australia/Sydney",
    datetime_local = 'dddd, MMMM Do YYYY, h:mm:ss a';

var formatDate = function (d) {
    return moment(d).format("ddd, hh:mmA");
};

var chart_types = {
    temp: {
        yAccessor: function (d) {
            return +d.temp / 100;
        },
        yFormat: function (d) {
            return d + "°C";
        }
    },
    pressure: {
        yAccessor: function (d) {
            return +d.pressure / 1000;
        },
        yFormat: function (d) {
            return (Math.round(d * 100) / 100) + "kPa";
        }
    },
    delay: {
        yAccessor: function (d) {
            return +d.delay;
        },
        yFormat: function (d) {
            return d + "ms";
        }
    },
    rssi: {
        yAccessor: function (d) {
            return +d.rssi;
        },
        yFormat: function (d) {
            return d;
        }
    }
};

export default Ember.Component.extend({
    brush_height: 40,
    height: 210,
    width: 960,
    margins: {
        top: 20,
        bottom: 20,
        left: 80,
        right: 20
    },
    _get: function (nm) {
        var vars = this.get('vars');

        if (nm in vars) {
            return vars[nm];
        }

        return this.get(nm);
    },
    vars: function () {
        var ct = this.get('chart-type');
        return chart_types[ct];
    }.property('chart-type'),
    xFormat: function (d) {
        return moment(d).fromNow();
    },
    didInsertElement: function () {

        var d = d3.select(this.$('#chart')[0]),
            _this = this,
            margin = this.get('margins'),
            bisectDate = d3.bisector(function (a) {
                return a.dt;
            }).left,
            width = this.get('width') - margin.left - margin.right,
            brush_height = this.get('brush_height'),
            height = this.get('height') - margin.top - margin.bottom;

        var svg = d.append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        svg.append("g")
            .attr("class", "x axis")
            .append("line")
            .attr("y1", -1)
            .attr("y2", -1)
            .attr("x1", 0)
            .attr("x2", width);

        svg.append("g")
            .attr("class", "y axis")
            .append("line")
            .attr("y1", -1)
            .attr("y2", height)
            .attr("x1", width)
            .attr("x2", width);


        var x = d3.time.scale()
            .range([0, width]);

        var y = d3.scale.linear()
            .range([height, 0]);

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom")
            .tickFormat(_this._get("xFormat"));

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left")
            .ticks(4)
            .tickFormat(_this._get("yFormat"));

        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);

        svg.append("g")
            .attr("class", "y axis")
            .call(yAxis);

        var focus = svg.append("g")
            .style("display", "none")
            .attr("class", "focus");

        focus.append("circle")
            .attr("class", "pin")
            .attr("r", 3);

        focus.append("line")
            .attr("class", "x")
            .attr("y1", 0)
            .attr("y2", height);

        focus.append("line")
            .attr("class", "y")
            .attr("x1", width)
            .attr("x2", width);


        this.set('x', x);
        this.set('y', y);
        this.set('height',height);
        this.set('xAxis',xAxis);
        this.set('yAxis',yAxis);
        this.set('svg', svg);

        svg.append("text")
            .attr("class", "value label-text")
            .attr('text-anchor', 'end')
            .attr("transform", 'translate(' + width + ',' + -2 + ')');

        svg.append("text")
            .attr("class", "dt label-text")
            .attr('text-anchor', 'start')
            .attr("transform", 'translate(' + 0 + ',' + -2 + ')');

        svg.append("rect")
            .attr("width", width)
            .attr("height", height)
            .style("fill", "none")
            .style("pointer-events", "all")
            .on("mouseover", function () {
                focus.style("display", null);
                svg.selectAll('.label-text').style('display', null);
            })
            .on("mouseout", function () {
                focus.style("display", "none");
                svg.selectAll('.label-text').style('display', 'none');
            })
            .on("mousemove", mousemove);

        function mousemove() {
            var x0 = x.invert(d3.mouse(this)[0]),
                i = bisectDate(data, x0, 1),
                d0 = data[i - 1],
                d1 = data[i],
                d = x0 - d0.dt > d1.dt - x0 ? d1 : d0;

            focus.select("circle.pin")
                .attr("transform",
                "translate(" + x(d.dt) + "," +
                y(_this._get('yAccessor')(d)) + ")");

            svg.select("text.value")
                .text(_this._get('yFormat')(_this._get('yAccessor')(d)));

            svg.select('text.dt')
                .text(formatDate(d.dt));

            focus.select(".x")
                .attr("transform",
                "translate(" + x(d.dt) + "," +
                y(_this._get('yAccessor')(d)) + ")")
                .attr("y2", height - y(_this._get('yAccessor')(d)));

            focus.select(".y")
                .attr("transform",
                "translate(" + width * -1 + "," +
                y(_this._get('yAccessor')(d)) + ")")
                .attr("x2", width + width);
        }

        this.drawData();
        //this.updateChart();

    },
    drawData: function () {

        var charts = this.get('charts'),
            _this = this,
            svg = this.get('svg'),
            x_ext = [],
            y_ext = [],
            series = [],
            height = this.get('height'),
            xAxis = this.get('xAxis'),
            yAxis = this.get('yAxis'),
            x = this.get('x'),
            y = this.get('y');

        var line = d3.svg.line()
            .x(function (d) {
                return x(d.dt);
            })
            .y(function (d) {
                return y(_this._get('yAccessor')(d));
            });


        charts.forEach(function (chart) {
            var
                _data = chart.get('obs'),
                data = [];

            d3.entries(_data).forEach(function (_) {
                _.value.dt = moment.utc(_.key).tz(tz).toDate();
                data.pushObject(_.value);
            });

            data = data.sort(function (a, b) {
                return a.dt - b.dt;
            });

            d3.extent(data, function (d) {
                return d.dt;
            })
                .forEach(function (e) {
                    x_ext.pushObject(e);
                });

            d3.extent(data, function (d) {
                return _this._get('yAccessor')(d);
            })
                .forEach(function (e) {
                    y_ext.pushObject(e);
                });

            series.pushObject(data);
        });

        x.domain(d3.extent(x_ext));
        y.domain(d3.extent(y_ext));

        series.forEach(function (s) {
            svg.append("path")
                .datum(s)
                .attr("class", "line")
                .attr("d", line);


        });

        d3.selectAll('.x.axis').selectAll('.tick').remove();
        svg.append("g")
            .attr("transform", "translate(0," + height + ")")
            .attr("class", "x axis")
            .call(xAxis);

        d3.selectAll('.y.axis').selectAll('.tick').remove();
        svg.append("g")
            .attr("class", "y axis")
            .call(yAxis);



    }.observes('charts', 'charts.[]')


});