import folium
import requests
import time
from flask import Flask, render_template_string


app = Flask(__name__)


@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                <title>ISS Tracker</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/leaflet.css" />
            </head>
            <body>
                <div id="map" style="height: 100vh;"></div>

                <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/leaflet.js"></script>
                <script>
                    var map = L.map('map').setView([0, 0], 2);

                    var tileLayer = L.tileLayer('https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png', {
                        maxZoom: 100,
                        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
                            '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
                            'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
                        id: 'mapbox.streets'
                    }).addTo(map);

                    var marker = L.marker([0, 0], { icon: L.icon({
                            iconUrl: 'https://www.metalearth.com/content/images/thumbs/0004022_international-space-station_1200.png',
                            iconSize: [32, 32],
                            iconAnchor: [16, 16],
                        }),
                        title: 'ISS'
                    }).addTo(map);

                    var polyline = L.polyline([], {color: 'red'}).addTo(map);

                    var path = [];
                    var currentZoom = 2;

                    function updateISS() {
                        fetch('http://api.open-notify.org/iss-now.json')
                            .then(response => response.json())
                            .then(data => {
                                var lat = parseFloat(data.iss_position.latitude);
                                var lon = parseFloat(data.iss_position.longitude);
                                marker.setLatLng([lat, lon]);
                                map.setView([lat, lon], currentZoom);
                                path.push([lat, lon]);
                                polyline.setLatLngs(path);
                            })
                            .catch(error => {
                                console.error('Error:', error);
                            });
                    }

                    map.on('zoomend', function() { 
                        currentZoom = map.getZoom();
                    });

                    setInterval(updateISS, 50);
                </script>
            </body>
        </html>
    ''')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
