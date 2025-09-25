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
          À qui appartient la parcelle ?
        </h1>

        <h1 className="text-4xl md:text-4xl font-bold mb-6 leading-tight">
        Déposez ici votre plan de terrain et vérifiez
        </h1>

        <div className="flex justify-center">
  <button
    onClick={handleCtaClick}
    className="w-full max-w-[400px] bg-accent hover:bg-yellow-800 text-primary-dark font-bold py-4 px-8 rounded-full text-lg shadow-lg transition-colors duration-300"
  ><h1 className="text-2xl md:text-4xl font-bold mb leading-tight">
  Vérifiez ici
  </h1>
  </button>
</div>

      </div>
      {/* Un fond stylisé si désiré, par exemple un pattern SVG ou une image de fond */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-dark to-primary opacity-50"></div>
    </section>
  );
};

export default Hero;