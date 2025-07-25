import requests
from flask import Flask, render_template_string, jsonify
from datetime import datetime
import time

app = Flask(__name__)

# Cache simples para os dados da ISS
iss_data_cache = {
    'timestamp': 0,
    'data': None
}

def get_iss_data():
    try:
        # Verifica se os dados em cache ainda são válidos (atualizados nos últimos 1 segundo)
        if time.time() - iss_data_cache['timestamp'] < 0 and iss_data_cache['data']:
            return iss_data_cache['data']
        
        response = requests.get('https://api.wheretheiss.at/v1/satellites/25544', timeout=5)
        response.raise_for_status()  # Levanta exceção para status codes 4xx/5xx
        
        data = response.json()
        
        # Formata os dados para nossa aplicação
        formatted_data = {
            'latitude': float(data['latitude']),
            'longitude': float(data['longitude']),
            'altitude': float(data['altitude']),
            'velocity': float(data['velocity']),
            'timestamp': data['timestamp'],
            'time': datetime.utcfromtimestamp(data['timestamp']).strftime('%H:%M:%S UTC')
        }
        
        # Atualiza o cache
        iss_data_cache['data'] = formatted_data
        iss_data_cache['timestamp'] = time.time()
        
        return formatted_data
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Erro ao processar dados: {e}")
        return None

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                <title>Rastreador ISS - Dados em Tempo Real</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
                    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
                    crossorigin=""/>
                <style>
                    body {
                        margin: 0;
                        padding: 0;
                        font-family: Arial, sans-serif;
                        overflow: hidden;
                    }
                    #map {
                        width: 100%;
                        height: 100vh;
                    }
                        #info-panel {
                        position: absolute;
                        top: 15px;
                        right: 15px;
                        z-index: 1000;
                        background: rgba(0, 5, 15, 0.85);
                        color: #e0f0ff;
                        padding: 15px;
                        border-radius: 10px;
                        box-shadow: 0 0 20px rgba(0, 100, 255, 0.3);
                        min-width: 260px;
                        border: 1px solid rgba(100, 180, 255, 0.2);
                    }
                    .data-row {
                        margin: 10px 0;
                        display: flex;
                        justify-content: space-between;
                    }
                    .data-label {
                        font-weight: bold;
                        color: #aaa;
                    }
                    .data-value {
                        color: white;
                        text-align: right;
                    }
                    #speed {
                        font-weight: bold;
                        font-size: 1.1em;
                    }
                    #last-update {
                        font-size: 0.8em;
                        color: #ccc;
                        text-align: right;
                        margin-top: 15px;
                        border-top: 1px solid #444;
                        padding-top: 8px;
                    }
                    .speed-meter {
                        height: 8px;
                        background: rgba(255, 255, 255, 0.2);
                        border-radius: 4px;
                        margin: 10px 0;
                        overflow: hidden;
                    }
                    .speed-bar {
                        height: 100%;
                        background: linear-gradient(to right, #2ecc71, #f1c40f, #e74c3c);
                        width: 0%;
                        transition: width 0.8s ease-out;
                    }
                    h3 {
                        margin: 0 0 10px 0;
                        color: #fff;
                        border-bottom: 1px solid #444;
                        padding-bottom: 8px;
                    }
                </style>
            </head>
            <body>
                <div id="map"></div>
                <div id="info-panel">
                    <h3>ESTAÇÃO ESPACIAL INTERNACIONAL</h3>
                    <div class="data-row">
                        <span class="data-label">Latitude:</span>
                        <span class="data-value" id="latitude">--</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">Longitude:</span>
                        <span class="data-value" id="longitude">--</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">Altitude:</span>
                        <span class="data-value" id="altitude">-- km</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">Velocidade:</span>
                        <span class="data-value"><span id="speed">--</span> km/h</span>
                    </div>
                    <div class="speed-meter">
                        <div class="speed-bar" id="speed-bar"></div>
                    </div>
                    <div id="last-update">Carregando dados...</div>
                </div>

                <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
                    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
                    crossorigin=""></script>
                <script>
                    // Configurações
                    const UPDATE_INTERVAL = 100; // 1 segundo
                    
                    // Inicializa o mapa
                    var map = L.map('map', {
                        minZoom: 2.5,
                        maxZoom: 10,
                        zoomControl: false
                    }).setView([0, 0], 2);
                    
                    // Usa tiles do OpenStreetMap
                    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                        subdomains: 'abcd',
                        maxZoom: 19
                    }).addTo(map);

                    // Cria o marcador da ISS
                    var marker = L.marker([0, 0], {
                        icon: L.icon({
                            iconUrl: 'https://cdn3d.iconscout.com/3d/premium/thumb/iss-5847493-4897839.png?f=webp',
                            iconSize: [90, 90],
                            iconAnchor: [50, 20],
                        }),
                        title: 'ISS'
                    }).addTo(map);

                    // Função para formatar números
                    function formatNumber(num, decimals) {
                        if (num === null || num === undefined) return '--';
                        return num.toLocaleString(undefined, {
                            minimumFractionDigits: decimals,
                            maximumFractionDigits: decimals
                        });
                    }

                    // Atualiza a exibição da velocidade
                    function updateSpeedDisplay(speed) {
                        const speedElement = document.getElementById('speed');
                        const speedBar = document.getElementById('speed-bar');
                        
                        if (!speed) {
                            speedElement.textContent = '--';
                            speedBar.style.width = '0%';
                            return;
                        }
                        
                        // Formata e exibe o valor
                        speedElement.textContent = formatNumber(speed, 0);
                        
                        // Calcula porcentagem para a barra (25,000-32,000 km/h como faixa)
                        const minSpeed = 25000;
                        const maxSpeed = 28000;
                        const percentage = Math.min(100, Math.max(0, ((speed - minSpeed) / (maxSpeed - minSpeed)) * 100));
                        speedBar.style.width = percentage + '%';
                        
                        // Atualiza cor baseada na velocidade
                        if (speed < 27000) {
                            speedElement.style.color = '#e74c3c';
                        } else if (speed < 28000) {
                            speedElement.style.color = '#f1c40f';
                        } else {
                            speedElement.style.color = '#2ecc71';
                        }
                    }

                    // Função para atualizar os dados
                    async function atualizarDados() {
                        try {
                            const response = await fetch('/iss_data');
                            if (!response.ok) {
                                throw new Error('Erro na resposta do servidor');
                            }
                            const data = await response.json();
                            
                            if (data && data.latitude !== undefined && data.longitude !== undefined) {
                                const lat = data.latitude;
                                const lon = data.longitude;
                                
                                // Atualiza apenas o marcador
                                marker.setLatLng([lat, lon]);
                                
                                // Atualiza informações
                                document.getElementById('latitude').textContent = formatNumber(lat, 4);
                                document.getElementById('longitude').textContent = formatNumber(lon, 4);
                                document.getElementById('altitude').textContent = formatNumber(data.altitude, 0) + ' km';
                                
                                // Atualiza velocidade
                                updateSpeedDisplay(data.velocity);
                                
                                // Atualiza horário
                                const updateText = data.time ? `Atualizado: ${data.time}` : `Atualizado: ${new Date().toLocaleTimeString()}`;
                                document.getElementById('last-update').textContent = updateText;
                                
                                // Centraliza o mapa suavemente
                                map.flyTo([lat, lon], map.getZoom(), {
                                    duration: 1,
                                    easeLinearity: 0.1
                                });
                            } else {
                                document.getElementById('last-update').textContent = 'Dados incompletos - ' + new Date().toLocaleTimeString();
                            }
                        } catch (error) {
                            console.error('Erro ao atualizar dados:', error);
                            document.getElementById('last-update').textContent = 'Erro na atualização - ' + new Date().toLocaleTimeString();
                        }
                    }

                    // Inicia a atualização
                    setInterval(atualizarDados, UPDATE_INTERVAL);
                    atualizarDados(); // Primeira chamada imediata
                </script>
            </body>
        </html>
    ''')

@app.route('/iss_data')
def iss_data():
    data = get_iss_data()
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Dados não disponíveis'}), 503

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
