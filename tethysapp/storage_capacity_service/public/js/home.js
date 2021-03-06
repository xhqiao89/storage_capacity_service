var map, click_point_layer, river_layer;
var outlet_x, outlet_y, damh, interval;

$(document).ready(function () {

    map = new ol.Map({
    layers: [ ],
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

    river_layer = new ol.layer.Tile({
        source: new ol.source.TileWMS({
            //url: 'https://geoserver.byu.edu/arcgis/services/sherry/utah_streams1k/MapServer/WMSServer?',
            url:'https://geoserver.byu.edu/arcgis/services/sherry/dr_streams/MapServer/WMSServer?',
            params: {'LAYERS': '0'},
            crossOrigin: 'anonymous'
        }),
        keyword: 'nwm'
    });

    map.addLayer(bing_layer);
    map.addLayer(river_layer);
    map.addLayer(click_point_layer);

    var lat = 18.9108;
    var lon = -71.2500;
    CenterMap(lat, lon);
    map.getView().setZoom(8);

    map.on('click', function(evt) {
        outlet_x = evt.coordinate[0];
        outlet_y = evt.coordinate[1];
        addClickPoint(evt.coordinate);
        //map.getView().setCenter(evt.coordinate);
        //map.getView().setZoom(16);

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



