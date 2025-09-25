import React from 'react';
import { useNavigate } from 'react-router-dom';

const Hero: React.FC = () => {
  const navigate = useNavigate();

  const handleCtaClick = () => {
    navigate('/upload');
  };

  return (
    <section className="bg-primary text-white py-20 md:py-32 text-center relative overflow-hidden">
      <div className="container mx-auto px-4 z-10 relative">
        <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
          Accès réel à une information foncière fiable
        </h1>
        <p className="text-2xl md:text-2xl mb-10 opacity-90 max-w-3xl mx-auto">
        Mi do gbe nu mi ɖo atɛjijɛ mitɔn ji
        </p>
        <button
          onClick={handleCtaClick}
          className="bg-accent hover:bg-yellow-600 text-primary-dark font-bold py-3 px-8 rounded-full text-lg shadow-lg transition-colors duration-300"
        >
          Commencez l'extraction
        </button>
      </div>
      {/* Un fond stylisé si désiré, par exemple un pattern SVG ou une image de fond */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-dark to-primary opacity-50"></div>
    </section>
  );
};

export default Hero;