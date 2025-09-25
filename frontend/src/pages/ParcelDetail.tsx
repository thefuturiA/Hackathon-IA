import React from 'react';
import { useParams } from 'react-router-dom';

const ParcelDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-primary-dark mb-4">Détail de la Parcelle #{id}</h1>
      <div className="bg-white p-6 rounded-lg shadow-md">
        <p className="text-text mb-4">
          Page de détail pour la parcelle avec l'ID: <span className="font-semibold">{id}</span>.
        </p>
        <p className="text-text">
          Cette page affichera les informations détaillées, les visualisations et les historiques
          relatifs à une parcelle spécifique. (Contenu à venir dans les étapes futures)
        </p>
        <div className="mt-6">
          <h2 className="text-xl font-semibold text-primary-dark mb-3">Informations Clés</h2>
          <ul className="list-disc list-inside text-text">
            <li>Propriétaire: [Nom du propriétaire]</li>
            <li>Superficie: [X] ha</li>
            <li>Usage: [Usage actuel]</li>
            <li>Date du dernier relevé: [Date]</li>
          </ul>
        </div>
        <div className="mt-6">
          <h2 className="text-xl font-semibold text-primary-dark mb-3">Visualisation</h2>
          <div className="w-full h-64 bg-gray-200 flex items-center justify-center text-gray-500 rounded-lg">
            [Zone pour la mini-carte de la parcelle / images]
          </div>
        </div>
      </div>
    </div>
  );
};

export default ParcelDetail;