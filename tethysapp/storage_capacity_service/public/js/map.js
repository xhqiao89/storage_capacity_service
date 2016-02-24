var map, click_point_layer;
var outlet_x, outlet_y, damh, interval;

var displayStatus = $('#display-status');

$(document).ready(function () {

    map = new ol.Map({
	layers: [ ],
	controls: ol.control.defaults(),
	target: 'map',
	view: new ol.View({
		zoom: 8,
        projection: "EPSG:3857"
	})
    });

    bing_layer = new ol.layer.Tile({

		source: new ol.source.BingMaps({
			imagerySet: 'AerialWithLabels',
			key: 'SFpNe1Al6IDxInoiI7Ta~LX-BVFN0fbUpmO4hIUm3ZA~AsJ3XqhA_0XVG1SUun4_ibqrBVYJ1XaYJdYUuHGqVCPOM71cx-3FS2FzCJCa2vIh'
		})
	});

    click_point_layer = new ol.layer.Vector({
      source: new ol.source.Vector(),
      style: new ol.style.Style({
        fill: new ol.style.Fill({
          color: 'rgba(255, 255, 255, 0.2)'
        }),
        stroke: new ol.style.Stroke({
          color: '#ffcc33',
          width: 2
        }),
        image: new ol.style.Circle({
          radius: 7,
          fill: new ol.style.Fill({
            color: '#ffcc33'
          })
        })
      })
    });

    map.addLayer(bing_layer);
    map.addLayer(click_point_layer);

    var lat = 18.9108;
    var lon = -71.2500;
    CenterMap(lat, lon);
    map.getView().setZoom(7);

    map.on('click', function(evt) {
        outlet_x = evt.coordinate[0];
        outlet_y = evt.coordinate[1];
        addClickPoint(evt.coordinate);
        map.getView().setCenter(evt.coordinate);
        map.getView().setZoom(15);

    })


    var chart_options = {
	chart: {
		renderTo: 'sc_chart',
		zoomType: 'x'
	},
        loading: {
            labelStyle: {
                top: '100%',
		        left: '100%',
                display: 'block',
                width: '100px',
                height: '100px',
                backgroundColor: '#000'
            }
        },
	title: {
		text: 'Storage Capacity Curve'
	},
    xAxis: {
		title: {
			text: 'Storage(m3)'
		}
		},
	yAxis: {
		title: {
			text: 'Elevation(m)'
		}
		},
	legend: {
		enabled: true
	},
    series: [{}]

};

    chart_options.series[0].type = 'line';
    chart_options.series[0].name = 'Elevation-Storage';

    chart = new Highcharts.Chart(chart_options);

});

function CenterMap(lat,lon){
    var dbPoint = {
        "type": "Point",
        "coordinates": [lon, lat]
    }
    var coords = ol.proj.transform(dbPoint.coordinates, 'EPSG:4326','EPSG:3857');
    map.getView().setCenter(coords);
}

function addClickPoint(coordinates){
    // Check if the feature exists. If not then create it.
    // If it does exist, then just change its geometry to the new coords.
    var geometry = new ol.geom.Point(coordinates);
    if (click_point_layer.getSource().getFeatures().length==0){
        var feature = new ol.Feature({
            geometry: geometry,
            attr: 'Some Property'
        });
        click_point_layer.getSource().addFeature(feature);
    } else {
        click_point_layer.getSource().getFeatures()[0].setGeometry(geometry);
    }
}

function run_sc_service() {

    damh = document.getElementById("damHeight").value;
    interval = document.getElementById("interval").value;
    alert(damh);
    alert(interval);
    alert(outlet_x);
    alert(outlet_y);

    displayStatus.removeClass('error');
    displayStatus.addClass('calculating');
    displayStatus.html('<em>Calculating...</em>');

    $.ajax({
        type: 'GET',
        url: 'sc-service/',
        dataType:'json',
        data: {
                'xlon': outlet_x,
                'ylat': outlet_y,
                'prj' : "native",
                'damh': damh,
                'interval': interval
                        },
        success: function (data) {

            if ('error' in data) {
                displayStatus.removeClass('calculating');
                displayStatus.addClass('error');
                displayStatus.html('<em>' + data.error + '</em>');
            }
            else
            {
                displayStatus.removeClass('calculating');
                displayStatus.addClass('success');
                displayStatus.html('<em>Success!</em>');
                //alert(data.SC_RESULT[0][0]);
                //alert(data.SC_RESULT.length)

                //var elev=[];
                //var stor=[];
                //for (i=0; i< data.SC_RESULT.length; i++){
                //    elev.push(parseFloat(data.SC_RESULT[i][1]));
                //    stor.push(parseFloat(data.SC_RESULT[i][0]));
                //}
                //alert(elev);
                //alert(stor);

                chart.series[0].setData(data.SC_RESULT);

           }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            alert("Error");
            debugger;
            $('#hydroshare-proceed').prop('disabled', false);
            console.log(jqXHR + '\n' + textStatus + '\n' + errorThrown);
            displayStatus.removeClass('uploading');
            displayStatus.addClass('error');
            displayStatus.html('<em>' + errorThrown + '</em>');
        }
    });

}

