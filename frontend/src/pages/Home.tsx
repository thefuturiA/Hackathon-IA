import React, { useEffect, useRef, useState } from 'react';
import Hero from '../components/Hero';
import Card from '../components/Card';
import ReliabilityIcon from '../assets/icon-reliability.svg';
import TopographicIcon from '../assets/icon-topographic.svg';
import InclusionIcon from '../assets/icon-inclusion.svg';
import './Home.css';

const Home: React.FC = () => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [showAdamChat, setShowAdamChat] = useState(false);
  const [isAdamSpeaking, setIsAdamSpeaking] = useState(false);
  const [adamMessage, setAdamMessage] = useState('');

  useEffect(() => {
    // Joue l'audio quand le composant est monté
    if (audioRef.current && !isMuted) {
      void audioRef.current.play().catch(error => {
        // Gère l'erreur si l'autoplay est bloqué par le navigateur
        console.log("Autoplay bloqué ou erreur de lecture :", error);
        // Optionnel: afficher un message à l'utilisateur pour qu'il clique pour jouer le son
      });
    }

    // Animation d'apparition d'Adam après 3 secondes
    const timer = setTimeout(() => {
      setIsAdamSpeaking(true);
      setAdamMessage('Bonjour ! Je suis Adam, votre assistant IA. Comment puis-je vous aider ?');
      setTimeout(() => {
        setIsAdamSpeaking(false);
      }, 4000);
    }, 3000);

    return () => clearTimeout(timer);
  }, [isMuted]);

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !audioRef.current.muted;
      setIsMuted(audioRef.current.muted);
    }
  };

  const handleAdamClick = () => {
    setShowAdamChat(!showAdamChat);
    if (!showAdamChat) {
      setIsAdamSpeaking(true);
      setAdamMessage('Comment puis-je vous assister aujourd\'hui ?');
      setTimeout(() => setIsAdamSpeaking(false), 3000);
    }
  };

  return (
    <div className="home-page">
      <Hero />
      <section className="container mx-auto px-4 py-12">
        <h2 className="text-3xl font-bold text-center mb-10 text-primary-dark">Nos Engagements</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card
            icon={ReliabilityIcon}
            title="Fiabilité de l'Information"
            description="Accédez à des données foncières vérifiées et à jour, pour des décisions éclairées et sécurisées."
          />
          <Card
            icon={TopographicIcon}
            title="Vérification Topographique"
            description="Des outils avancés pour l'analyse topographique, garantissant l'exactitude des limites parcellaires."
          />
          <Card
            icon={InclusionIcon}
            title="Inclusion et Accès Équitable"
            description="Faciliter l'accès à l'information foncière pour tous, contribuant à une gestion plus juste du territoire."
          />
        </div>
      </section>

      {/* Lecteur audio de bienvenue */}
      <audio ref={audioRef} src="/audio/agonoumi.mp3" loop />
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={toggleMute}
          className="bg-primary-dark text-white p-3 rounded-full shadow-lg hover:bg-primary transition-colors duration-200"
          aria-label={isMuted ? "Unmute audio" : "Mute audio"}
        >
          {isMuted ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.293 17.293A8 8 0 015.707 5.707m1.414 1.414a6 6 0 007.952 7.952m-1.414 1.414L10 14.5M15.5 11.5L21 16m-5.5-1.5L12 11.5L6.5 14L2 10.5l4.5-3.5" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464A5 5 0 0117 12h-2m-7 4H5a2 2 0 01-2-2V8a2 2 0 012-2h3.586a1 1 0 01.707.293L10 7.586V16a1 1 0 01-1.707.707l-3.586-3.586z" />
            </svg>
          )}
        </button>
      </div>

      {/* Adam - Assistant IA Animé */}
      <div className="fixed bottom-6 left-6 z-50">
        {/* Bulle de message */}
        {(isAdamSpeaking || showAdamChat) && adamMessage && (
          <div className="absolute bottom-28 left-0 mb-2 animate-bounce">
            <div className="bg-white border-3 border-yellow-500 rounded-xl p-4 shadow-2xl max-w-sm relative">
              <p className="text-sm text-gray-800 font-medium">{adamMessage}</p>
              <div className="absolute bottom-0 left-10 w-0 h-0 border-l-10 border-r-10 border-t-10 border-l-transparent border-r-transparent border-t-yellow-500 transform translate-y-full"></div>
            </div>
          </div>
        )}

        {/* Chat Panel */}
        {showAdamChat && (
          <div className="absolute bottom-28 left-0 bg-white rounded-xl shadow-2xl border-3 border-yellow-500 w-80 h-96 animate-in slide-in-from-bottom duration-300">
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-t-xl">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg">
                  <span className="text-xl">🤖</span>
                </div>
                <span className="font-bold text-white text-lg">Adam IA</span>
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse shadow-lg"></div>
              </div>
              <button 
                onClick={() => setShowAdamChat(false)}
                className="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-4 h-64 overflow-y-auto">
              <div className="space-y-3">
                <div className="bg-gradient-to-r from-gray-100 to-gray-50 rounded-xl p-4 shadow-sm">
                  <p className="text-sm text-gray-800 font-medium">
                    Bonjour ! Je suis Adam, votre assistant intelligent. Je peux vous aider avec :
                  </p>
                  <ul className="text-xs text-gray-600 mt-3 space-y-2">
                    <li className="flex items-center space-x-2">
                      <span className="w-2 h-2 bg-yellow-400 rounded-full"></span>
                      <span>Questions sur les données foncières</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="w-2 h-2 bg-orange-400 rounded-full"></span>
                      <span>Navigation sur la plateforme</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="w-2 h-2 bg-yellow-400 rounded-full"></span>
                      <span>Support technique</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="w-2 h-2 bg-orange-400 rounded-full"></span>
                      <span>Conseils et recommandations</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 p-4 border-t-2 border-yellow-200">
              <div className="flex space-x-2">
                <input 
                  type="text" 
                  placeholder="Tapez votre question..."
                  className="flex-1 px-4 py-2 border-2 border-gray-300 rounded-lg text-sm focus:outline-none focus:border-yellow-500 focus:ring-2 focus:ring-yellow-200"
                />
                <button className="px-5 py-2 bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white rounded-lg text-sm font-bold transition-all shadow-lg hover:shadow-xl transform hover:scale-105">
                  Envoyer
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Icône Adam principale - TAILLE AUGMENTÉE */}
        <button
          onClick={handleAdamClick}
          className="relative group"
        >
          {/* Cercles d'animation plus grands */}
          <div className="absolute inset-0 -m-4">
            <div className="w-28 h-28 border-4 border-yellow-400/40 rounded-full animate-ping"></div>
          </div>
          <div className="absolute inset-0 -m-3">
            <div className="w-26 h-26 border-3 border-orange-400/60 rounded-full animate-pulse"></div>
          </div>
          <div className="absolute inset-0 -m-2">
            <div className="w-24 h-24 border-2 border-yellow-300/50 rounded-full animate-ping animation-delay-150"></div>
          </div>
          
          {/* Corps principal plus grand */}
          <div className="relative w-20 h-20 bg-gradient-to-br from-yellow-400 via-yellow-500 to-orange-600 rounded-full flex items-center justify-center shadow-2xl transform transition-all duration-300 hover:scale-125 hover:shadow-3xl animate-bounce hover:animate-pulse">
            {/* Effet de brillance renforcé */}
            <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/40 to-transparent rounded-full"></div>
            <div className="absolute inset-0 bg-gradient-to-bl from-transparent via-yellow-200/30 to-transparent rounded-full"></div>
            
            {/* Visage d'Adam plus grand */}
            <div className="relative z-10">
              {/* Yeux plus grands */}
              <div className="flex space-x-3 mb-2">
                <div className={`w-3 h-3 bg-white rounded-full shadow-sm transition-all duration-200 ${isAdamSpeaking ? 'animate-pulse scale-110' : ''}`}>
                  <div className="w-1 h-1 bg-blue-500 rounded-full ml-1 mt-1"></div>
                </div>
                <div className={`w-3 h-3 bg-white rounded-full shadow-sm transition-all duration-200 ${isAdamSpeaking ? 'animate-pulse scale-110' : ''}`}>
                  <div className="w-1 h-1 bg-blue-500 rounded-full ml-1 mt-1"></div>
                </div>
              </div>
              
              {/* Bouche plus visible */}
              <div className={`w-4 h-2 bg-white rounded-full shadow-sm transition-all duration-300 ${isAdamSpeaking ? 'animate-ping scale-125' : ''}`}></div>
              
              {/* Particules plus nombreuses et visibles */}
              <div className="absolute -top-3 -right-3 w-2 h-2 bg-yellow-200 rounded-full animate-ping animation-delay-300"></div>
              <div className="absolute -bottom-2 -left-3 w-2 h-2 bg-orange-300 rounded-full animate-pulse animation-delay-500"></div>
              <div className="absolute top-2 -left-4 w-1 h-1 bg-yellow-300 rounded-full animate-bounce animation-delay-700"></div>
              <div className="absolute -top-1 left-6 w-1 h-1 bg-orange-200 rounded-full animate-ping animation-delay-900"></div>
              <div className="absolute bottom-4 right-5 w-1 h-1 bg-yellow-400 rounded-full animate-pulse animation-delay-1100"></div>
            </div>

            {/* Badge "IA" plus grand */}
            <div className="absolute -top-2 -right-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white text-sm font-bold rounded-full w-8 h-8 flex items-center justify-center animate-pulse shadow-lg border-2 border-white">
              IA
            </div>

            {/* Indicateur de notification plus visible */}
            {!showAdamChat && (
              <div className="absolute -top-2 -left-2 w-4 h-4 bg-gradient-to-r from-red-500 to-red-600 rounded-full animate-bounce flex items-center justify-center shadow-lg border-2 border-white">
                <div className="w-2 h-2 bg-white rounded-full animate-ping"></div>
              </div>
            )}

            {/* Effet de halo lumineux */}
            <div className="absolute inset-0 -m-1 bg-gradient-to-r from-yellow-400/20 to-orange-400/20 rounded-full blur-sm animate-pulse"></div>
          </div>

          {/* Nom en dessous plus visible */}
          <div className="absolute -bottom-10 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
            <span className="text-sm font-bold text-yellow-700 bg-white/95 px-3 py-2 rounded-full shadow-lg border-2 border-yellow-200 animate-pulse">
              Adam
            </span>
          </div>
        </button>
      </div>


    </div>
  );
};

export default Home;