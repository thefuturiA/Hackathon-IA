import React, { useEffect, useRef, useState } from 'react';
import Hero from '../components/Hero';
import Card from '../components/Card';
import ReliabilityIcon from '../assets/icon-reliability.svg';
import TopographicIcon from '../assets/icon-topographic.svg';
import InclusionIcon from '../assets/icon-inclusion.svg';

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
      <audio ref={audioRef} src="/audio/bienvenue.mp3" loop />

      {/* Icônes fixes à droite */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col space-y-4">
        {/* Adam - Assistant IA Animé - DÉPLACÉ À DROITE */}
        <div className="relative">
          {/* Bulle de message */}
          {(isAdamSpeaking || showAdamChat) && adamMessage && (
            <div className="absolute bottom-24 -left-80 mb-2 animate-bounce">
              <div className="bg-white border-3 border-yellow-500 rounded-xl p-4 shadow-2xl max-w-sm relative">
                <p className="text-sm text-gray-800 font-medium">{adamMessage}</p>
                <div className="absolute bottom-0 right-10 w-0 h-0 border-l-10 border-r-10 border-t-10 border-l-transparent border-r-transparent border-t-yellow-500 transform translate-y-full"></div>
              </div>
            </div>
          )}

          {/* Chat Panel */}
          {showAdamChat && (
            <div className="absolute bottom-24 -left-80 bg-white rounded-xl shadow-2xl border-3 border-yellow-500 w-80 h-96 animate-in slide-in-from-bottom duration-300">
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
          </button>
        </div>

        {/* Bouton audio mute/unmute - REDESIGNÉ */}
        <button
          onClick={toggleMute}
          className={`relative w-16 h-16 rounded-full shadow-2xl transition-all duration-300 hover:scale-110 transform ${
            isMuted 
              ? 'bg-gradient-to-r from-red-500 via-red-600 to-red-700 hover:from-red-600 hover:to-red-800' 
              : 'bg-gradient-to-r from-green-500 via-green-600 to-green-700 hover:from-green-600 hover:to-green-800'
          }`}
          aria-label={isMuted ? "Activer le son" : "Couper le son"}
        >
          {/* Effet de brillance */}
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/30 to-transparent rounded-full"></div>
          
          {/* Icône son */}
          <div className="relative z-10 flex items-center justify-center h-full">
            {isMuted ? (
              // Icône son coupé - PLUS CLAIRE
              <div className="relative">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
                </svg>
                {/* Ligne de coupure plus visible */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-10 h-0.5 bg-white rounded-full rotate-45 shadow-lg"></div>
                </div>
              </div>
            ) : (
              // Icône son activé - PLUS CLAIRE
              <div className="relative">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
                </svg>
                {/* Ondes sonores animées */}
                <div className="absolute -right-1 top-1/2 transform -translate-y-1/2">
                  <div className="w-1 h-1 bg-white rounded-full animate-ping animation-delay-0"></div>
                </div>
                <div className="absolute -right-2 top-1/2 transform -translate-y-1/2">
                  <div className="w-1 h-1 bg-white rounded-full animate-ping animation-delay-300"></div>
                </div>
                <div className="absolute -right-3 top-1/2 transform -translate-y-1/2">
                  <div className="w-1 h-1 bg-white rounded-full animate-ping animation-delay-600"></div>
                </div>
              </div>
            )}
          </div>

          {/* Badge d'état */}
          <div className={`absolute -top-1 -right-1 w-5 h-5 rounded-full border-2 border-white shadow-lg flex items-center justify-center text-xs font-bold ${
            isMuted ? 'bg-red-500 text-white' : 'bg-green-400 text-green-900'
          }`}>
            {isMuted ? '✕' : '♪'}
          </div>

          {/* Effet de halo */}
          <div className={`absolute inset-0 -m-2 rounded-full blur-sm animate-pulse ${
            isMuted 
              ? 'bg-red-500/30' 
              : 'bg-green-500/30'
          }`}></div>
        </button>
      </div>

      {/* Styles CSS additionnels pour Adam */}
      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-15px); }
        }
        
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 30px rgba(251, 191, 36, 0.6); }
          50% { box-shadow: 0 0 50px rgba(251, 191, 36, 1); }
        }
        
        @keyframes ultraGlow {
          0%, 100% { 
            box-shadow: 0 0 40px rgba(251, 191, 36, 0.8), 
                        0 0 80px rgba(249, 115, 22, 0.4),
                        0 0 120px rgba(251, 191, 36, 0.2);
          }
          50% { 
            box-shadow: 0 0 60px rgba(251, 191, 36, 1), 
                        0 0 120px rgba(249, 115, 22, 0.6),
                        0 0 180px rgba(251, 191, 36, 0.4);
          }
        }
        
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
        
        .animate-glow {
          animation: glow 2s ease-in-out infinite;
        }
        
        .animate-ultra-glow {
          animation: ultraGlow 3s ease-in-out infinite;
        }
        
        .animation-delay-0 { animation-delay: 0ms; }
        .animation-delay-150 { animation-delay: 150ms; }
        .animation-delay-300 { animation-delay: 300ms; }
        .animation-delay-500 { animation-delay: 500ms; }
        .animation-delay-600 { animation-delay: 600ms; }
        .animation-delay-700 { animation-delay: 700ms; }
        .animation-delay-900 { animation-delay: 900ms; }
        .animation-delay-1100 { animation-delay: 1100ms; }
        
        .shadow-3xl {
          box-shadow: 0 35px 60px -12px rgba(0, 0, 0, 0.25), 
                      0 0 40px rgba(251, 191, 36, 0.3);
        }
        
        .border-3 {
          border-width: 3px;
        }
        
        .border-l-10, .border-r-10, .border-t-10 {
          border-width: 10px;
        }
      `}</style>
    </div>
  );
};

export default Home;