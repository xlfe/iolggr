import Em from 'ember';
//import d3 from 'd3';
/* global d3 */
/* global moment */

var formatDate = function (d) {
    return moment(d).format("ddd, hh:mmA");
};

var chart_types = {
    temp: {
        yAccessor: function (d) {
            return +d.temp / 100;
        },
        yFormat: function (d) {
            if ((d%1) !== 0){
                return d.toFixed(1) + "°C";
            } else {
                return d.toFixed(0) + "°C";
            }
        }
    },
    pressure: {
        yAccessor: function (d) {
            return +d.pressure / 1000;
        },
        yFormat: function (d) {
            if ((d%1) !== 0){
                return (Math.round(d * 100) / 100).toFixed(1) + "kPa";
            } else {
                return (Math.round(d * 100) / 100).toFixed(0) + "kPa";
            }
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

export default Em.Component.extend({
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
        if (moment().diff(d,'seconds') < 30) {
            return 'now';
        }
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
            //brush_height = this.get('brush_height'),
            charts = this.get('charts'),
            x_ext = [],
            y_ext = [],
            series = [],
            height = this.get('height') - margin.top - margin.bottom;

        d.select('svg').remove();
        if(Em.isEmpty(charts)){
            return;
        }

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

        charts.forEach(function (chart) {
            var data = chart.get('_obs');

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

            series.pushObject({
                data: data,
                id: chart.get('id'),
                name: chart.get('name'),
                colour: chart.get('colour')
            });
        });

        if (moment().diff(x_ext[1],'minutes') <=5){
            x_ext[1] = moment().toDate();
        }

        var x_tp = moment(x_ext[1]).diff(x_ext[0],'seconds'),
            x_ticks = d3.range(5).map(function(i){
                return moment(x_ext[0]).add((i*x_tp)/5.0,'seconds').toDate();
            });
        x_ticks.pushObject(x_ext[1]);

        y_ext = d3.extent(y_ext);
        if(y_ext[0] % 1 !== 0 || y_ext[1] %1 !== 0){
            y_ext[0] = Math.floor(y_ext[0]);
            y_ext[1] = Math.ceil(y_ext[1]);
        }


        var x = d3.time.scale()
            .range([0, width])
            .domain(d3.extent(x_ext));

        var y = d3.scale.linear()
            .range([height, 0])
            .domain(d3.extent(y_ext))
            .nice();


        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom")
            .tickValues(x_ticks)
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

        var line = d3.svg.line()
            .x(function (d) {
                return x(d.dt);
            })
            .y(function (d) {
                return y(_this._get('yAccessor')(d));
            });


        series.forEach(function (s) {
            svg.append("path")
                .datum(s.data)
                .attr("class", "line colour-"+s.colour)
                .attr("d", line);
        });

        var focus = svg.append("g")
            .style("display", "none")
            .attr("class", "focus");

        series.forEach(function(s){

            focus.append("circle")
                .attr("class", "pin dev-"+s.id)
                .attr("r", 3);

            focus.append("line")
                .attr("class", "y dev-"+s.id)
                .attr("x1", width)
                .attr("x2", width);

            svg.append("text")
                .attr("class", "value label-text dev-"+s.id)
                .attr('text-anchor', 'start')
                .attr("transform", 'translate(' + 0 + ',' + -2 + ')');


        });

        focus.append("line")
            .attr("class", "x")
            .attr("y1", 0)
            .attr("y2", height);

        svg.append("text")
            .attr("class", "dt label-text")
            .attr('text-anchor', 'end')
            .attr("transform", 'translate(' + width + ',' + -2 + ')');

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
                text = [];

            series.forEach(function(s){

                var data = s.data,
                    i = bisectDate(data, x0, 1),
                    d0 = data[i - 1],
                    d1 = data[i],
                    d = x0 - d0.dt > d1.dt - x0 ? d1 : d0;

                focus
                    .select("circle.pin.dev-"+s.id)
                    .attr("transform","translate(" + x(d.dt) + "," + y(_this._get('yAccessor')(d)) + ")");

                text.pushObject(s.name +": " + _this._get('yFormat')(_this._get('yAccessor')(d)));

                focus
                    .select(".y.dev-"+s.id)
                    .attr("transform", "translate(" + width * -1 + "," + y(_this._get('yAccessor')(d)) + ")")
                    .attr("x2", width + width);

            });

            focus
                .select(".x")
                .attr("transform", "translate(" + x(x0) + ",0)")// + y(_this._get('yAccessor')(d)) + ")")
                .attr("y2", height);// - y(_this._get('yAccessor')(d)));


            svg.select("text.value")
                .text(text.join(', '));

            svg.select('text.dt')
                .text(formatDate(x0));

        }

    }.observes('charts', 'charts.[]')
});