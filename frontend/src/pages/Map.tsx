import React from 'react';

const Map: React.FC = () => {
  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold text-primary-dark mb-4">Carte Interactive</h1>
      <p className="text-text">Page Carte (placeholder) - La carte interactive sera implémentée ici à l'étape 2.</p>
      <div className="w-full h-96 bg-gray-200 flex items-center justify-center text-gray-500 rounded-lg mt-4">
        [Zone pour la carte Leaflet]
      </div>
    </div>
  );
};

export default Map;