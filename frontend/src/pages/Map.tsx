import React, { useState } from 'react';
import { Layers, Satellite, Map as MapIcon, Navigation, ZoomIn, ZoomOut, Home } from 'lucide-react';

const Map: React.FC = () => {
  const [currentLayer, setCurrentLayer] = useState('satellite');

  const layers = [
    { 
      id: 'satellite', 
      name: 'Vue Satellite', 
      icon: Satellite,
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    },
    { 
      id: 'streets', 
      name: 'Plan de Ville', 
      icon: MapIcon,
      url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
    }
  ];

  // Coordonnées du Bénin
  const beninCenter = { lat: 9.30769, lng: 2.315834 };

  return (
    <div className="relative h-screen w-full overflow-hidden">
      {/* En-tête simple */}
      <div className="absolute top-0 left-0 right-0 bg-white/90 backdrop-blur-sm shadow-sm z-20 p-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900 flex items-center">
            🇧🇯 <span className="ml-2">Carte du Bénin</span>
          </h1>
          
          {/* Sélecteur de couche */}
          <div className="flex items-center space-x-2 bg-white rounded-lg shadow-sm p-1">
            {layers.map((layer) => (
              <button
                key={layer.id}
                onClick={() => setCurrentLayer(layer.id)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-all ${
                  currentLayer === layer.id
                    ? 'bg-blue-100 text-blue-700 shadow-sm'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <layer.icon className="w-4 h-4" />
                <span className="text-sm font-medium">{layer.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Iframe avec carte réelle */}
      <div className="absolute top-16 left-0 right-0 bottom-0">
        {currentLayer === 'satellite' ? (
          // Vue Satellite via Esri
          <iframe
            src={`https://www.arcgis.com/apps/Embed/index.html?webmap=10df2279f9684e4a9f6a7f08febac2a9&extent=${beninCenter.lng-2},${beninCenter.lat-2},${beninCenter.lng+2},${beninCenter.lat+2}&zoom=true&previewImage=false&scale=true&disable_scroll=true&theme=light`}
            width="100%"
            height="100%"
            frameBorder="0"
            style={{ border: 'none' }}
            allowFullScreen
            title="Carte Satellite du Bénin"
          />
        ) : (
          // Vue Plan via OpenStreetMap
          <iframe
            src={`https://www.openstreetmap.org/export/embed.html?bbox=${beninCenter.lng-3}%2C${beninCenter.lat-3}%2C${beninCenter.lng+3}%2C${beninCenter.lat+3}&layer=mapnik&marker=${beninCenter.lat}%2C${beninCenter.lng}`}
            width="100%"
            height="100%"
            frameBorder="0"
            style={{ border: 'none' }}
            title="Plan du Bénin"
          />
        )}
      </div>

      {/* Alternative avec Leaflet (plus personnalisable) */}
      <div className="absolute top-16 left-0 right-0 bottom-0 hidden" id="leaflet-map">
        <div className="w-full h-full bg-gray-100 flex items-center justify-center">
          <div className="text-center bg-white p-6 rounded-lg shadow-lg">
            <div className="text-4xl mb-4">🗺️</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Carte Interactive</h2>
            <p className="text-gray-600 mb-4">
              Pour une carte plus personnalisable, installez :
            </p>
            <code className="bg-gray-900 text-green-400 px-4 py-2 rounded text-sm block">
              npm install leaflet react-leaflet
            </code>
          </div>
        </div>
      </div>

      {/* Contrôles de navigation */}
      <div className="absolute top-24 right-4 z-10 flex flex-col space-y-2">
        <button className="bg-white hover:bg-gray-50 p-2 rounded-lg shadow-sm transition-colors">
          <ZoomIn className="w-5 h-5 text-gray-700" />
        </button>
        <button className="bg-white hover:bg-gray-50 p-2 rounded-lg shadow-sm transition-colors">
          <ZoomOut className="w-5 h-5 text-gray-700" />
        </button>
        <button className="bg-white hover:bg-gray-50 p-2 rounded-lg shadow-sm transition-colors">
          <Navigation className="w-5 h-5 text-gray-700" />
        </button>
        <button className="bg-white hover:bg-gray-50 p-2 rounded-lg shadow-sm transition-colors">
          <Home className="w-5 h-5 text-gray-700" />
        </button>
      </div>

      {/* Informations en bas */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-sm p-3 z-10">
        <div className="text-sm text-gray-700">
          <div className="font-medium">🌍 République du Bénin</div>
          <div className="text-gray-500">
            {currentLayer === 'satellite' ? 'Vue satellite haute résolution' : 'Plan détaillé des villes'}
          </div>
        </div>
      </div>

      {/* Coordonnées temps réel (simulées) */}
      <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-sm p-3 z-10">
        <div className="text-xs text-gray-600 font-mono">
          <div>Lat: {beninCenter.lat}°N</div>
          <div>Lng: {beninCenter.lng}°E</div>
          <div className="text-green-600 mt-1">● Connexion active</div>
        </div>
      </div>
    </div>
  );
};

export default Map;