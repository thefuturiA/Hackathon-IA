import React from 'react';

const Map: React.FC = () => {
  return (
    <div className="h-screen w-full">
      {/* En-tête simple */}
      <div className="absolute top-0 left-0 right-0 bg-white shadow-md z-10 p-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">🗺️ Carte du Bénin</h1>
          <div className="text-sm text-gray-600">
            Carte interactive en temps réel
          </div>
        </div>
      </div>

      {/* Zone de carte - Version iframe OpenStreetMap */}
      <div className="pt-16 h-full">
        <iframe
          src="https://www.openstreetmap.org/export/embed.html?bbox=0.7751%2C6.0394%2C3.8564%2C12.4089&amp;layer=mapnik&amp;marker=9.3077%2C2.3158"
          style={{
            border: 0,
            width: '100%',
            height: '100%'
          }}
          title="Carte du Bénin - OpenStreetMap"
        />
      </div>

      {/* Contrôles flottants */}
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 z-10">
        <div className="text-sm font-medium text-gray-900 mb-2">🇧🇯 République du Bénin</div>
        <div className="text-xs text-gray-600">
          Carte fournie par OpenStreetMap
        </div>
      </div>

      {/* Instructions */}
      <div className="absolute top-20 right-4 bg-blue-50 border border-blue-200 rounded-lg p-4 z-10 max-w-sm">
        <h3 className="font-semibold text-blue-900 mb-2">💡 Navigation</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Cliquez et glissez pour naviguer</li>
          <li>• Molette pour zoomer/dézoomer</li>
          <li>• Double-clic pour zoomer rapidement</li>
        </ul>
        
        <div className="mt-3 pt-3 border-t border-blue-200">
          <div className="text-xs text-blue-600">
            <strong>Centré sur :</strong> Bénin (9.31°N, 2.32°E)<br/>
            <strong>Zoom :</strong> Vue pays entier
          </div>
        </div>
      </div>
    </div>
  );
};

export default Map;