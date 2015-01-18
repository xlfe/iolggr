import Ember from 'ember';
//import d3 from 'd3';

export default Ember.Component.extend({
    didInsertElement: function () {
        var data = this.get('data'),
            d = d3.select(this.$('#chart')[0])

        var margin = {top: 20, right: 20, bottom: 30, left: 50},
            width = 960 - margin.left - margin.right,
            height = 500 - margin.top - margin.bottom;

        var parseDate = d3.time.format("%Y-%m-%dT%H:%M:%S").parse;

        var x = d3.time.scale()
            .range([0, width]);

        var y = d3.scale.linear()
            .range([height, 0]);

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom");

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left");

        var line = d3.svg.line()
            .x(function (d) {
                return x(d.dt);
            })
            .y(function (d) {
                return y(d.temp);
            });

        var svg = d.append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        data.forEach(function (d) {
            d.dt = parseDate(d.dt);
            console.log(d);
        });

        x.domain(d3.extent(data, function (d) {
            return d.dt;
        }));
        y.domain(d3.extent(data, function (d) {
            return d.temp;
        }));

        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);

        svg.append("g")
            .attr("class", "y axis")
            .call(yAxis)
            .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text("Temp (C)");

        svg.append("path")
            .datum(data)
            .attr("class", "line")
            .attr("d", line);


        console.log("on the page!", d);
    }
});