var map, click_point_layer,river_layer, basin_layer;
var outlet_x, outlet_y, damh, interval;

var displayStatus = $('#display-status');

$(document).ready(function () {

    map = new ol.Map({
    layers: [],
    controls: ol.control.defaults(),
    target: 'map',
    view: new ol.View({
		zoom: 10,
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

    river_layer = new ol.layer.Vector({
        source: new ol.source.Vector({
            url: "/static/storage_capacity_service/kml/dr_stream_lines_1k.kml",
      format: new ol.format.KML(),
     })
  });

    basin_layer = new ol.layer.Vector({
        source: new ol.source.Vector({
            features: new ol.format.GeoJSON()
        }),
        style: new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: 'blue',
            lineDash: [4],
            width: 3
            }),
        fill: new ol.style.Fill({
            color: 'rgba(0, 0, 255, 0.1)'
            })
        })
    });

    map.addLayer(bing_layer);
    map.addLayer(click_point_layer);
    map.addLayer(river_layer);
    map.addLayer(basin_layer);

    var lat = 18.9108;
    var lon = -71.2500;
    CenterMap(lat, lon);
    map.getView().setZoom(8);

    map.on('click', function(evt) {
    var feature = map.forEachFeatureAtPixel(evt.pixel, function(feature, layer) {
                return feature;
            }, null, function(layer) {
                return layer === river_layer;
            });

            if(feature){
                //alert(feature);
                addClickPoint(evt.coordinate);
                var coordinate = evt.coordinate;
                outlet_x = coordinate[0];
                outlet_y = coordinate[1];
                map.getView().setCenter(evt.coordinate);
                map.getView().setZoom(18);
            }
    });

});

function CenterMap(lat,lon){
    var dbPoint = {
        "type": "Point",
        "coordinates": [lon, lat]
    };
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

    $.ajax({
        type: 'GET',
        url: '/apps/storage-capacity-service/run',
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
                alert("Error");
            }
            else
            {
                window.open("/apps/storage-capacity-service/joblist");

           }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            alert("Error");
        }
    });

}

function geojson2feature(myGeoJSON) {
    //Convert GeoJSON object into an OpenLayers 3 feature.
    var geojsonformatter = new ol.format.GeoJSON();
    var myFeature = geojsonformatter.readFeatures(myGeoJSON);
    //var myFeature = new ol.Feature(myGeometry);
    return myFeature;

}

function run_watershed_delin() {

    alert(outlet_x);
    alert(outlet_y);

    basin_layer.getSource().clear();
    $('#btnDelin').addClass('disabled');

    displayStatus.removeClass('error');
    displayStatus.addClass('calculating');
    displayStatus.html('<em>Calculating...</em>');

    $.ajax({
        type: 'GET',
        url: 'waterdelin',
        dataType:'json',
        data: {
                'xlon': outlet_x,
                'ylat': outlet_y,
                'prj' : "native"
        },
        success: function (data) {

            $('#btnDelin').removeClass('disabled');
            alert(data.status)
            basin_layer.getSource().addFeatures(geojson2feature(data.GeoJSON));
            displayStatus.removeClass('calculating');
            displayStatus.addClass('success');
            displayStatus.html('<em>Success!</em>');

        },
        error: function (jqXHR, textStatus, errorThrown) {
            $('#btnDelin').removeClass('disabled');
            alert("Error");
            displayStatus.removeClass('calculating');
            displayStatus.addClass('error');
            displayStatus.html('<em>' + errorThrown + '</em>');
        }
    });

}

function run_geocoder() {
    g = new google.maps.Geocoder();
    myAddress=document.getElementById('txtLocation').value;
    g.geocode({'address': myAddress}, geocoder_success);
}

function geocoder_success(results, status) {
    if (status == google.maps.GeocoderStatus.OK) {
        r=results;
        flag_geocoded=true;
        Lat = results[0].geometry.location.lat();
        Lon = results[0].geometry.location.lng();

        var dbPoint = {
            "type": "Point",
            "coordinates": [Lon, Lat]
        }

        var coords = ol.proj.transform(dbPoint.coordinates, 'EPSG:4326','EPSG:3857');
        //addClickPoint(coords);
        CenterMap(Lat,Lon);
        map.getView().setZoom(14);

    } else {
        alert("Geocode was not successful for the following reason: " + status);
    }
}
function handle_search_key(e) {
    // Handle a key press in the location search text box.
    // This handles pressing the enter key to initiate the search.
    if (e.keyCode == 13) {
        run_geocoder();
    }
}


