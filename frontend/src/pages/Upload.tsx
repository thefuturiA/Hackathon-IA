import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, File, X, CheckCircle2 } from 'lucide-react';

const Upload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    // Joue l'audio quand le composant est monté
    if (audioRef.current && !isMuted) {
      void audioRef.current.play().catch(error => {
        // Gère l'erreur si l'autoplay est bloqué par le navigateur
        console.log("Autoplay bloqué ou erreur de lecture :", error);
      });
    }
  }, [isMuted]);

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !audioRef.current.muted;
      setIsMuted(audioRef.current.muted);
    }
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  const navigate = useNavigate();
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile) {
      // Logique d'envoi du fichier
      console.log('Envoi du fichier:', selectedFile.name);
      navigate('/map');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-primary-dark mb-3">
          Déposer votre levé topographique
        </h1>
        <p className="text-text text-lg opacity-75">
          Sélectionnez et envoyez votre document depuis votre appareil
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl overflow-hidden">
        {/* Header du formulaire */}
        <div className="bg-gradient-to-r from-primary to-primary-dark p-6">
          <div className="flex items-center space-x-3">
            <div className="bg-white/20 p-3 rounded-full">
              <UploadIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Votre document</h2>
              <p className="text-white/80 text-sm">Formats acceptés: PDF, DWG, DXF, JPG, PNG</p>
            </div>
          </div>
        </div>

        {/* Zone de contenu */}
        <div className="p-8">
          {/* Zone de drop/sélection de fichier */}
          <div className="mb-8">
            <div
              className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
                dragActive
                  ? 'border-primary bg-primary/5 scale-105'
                  : selectedFile
                  ? 'border-green-400 bg-green-50'
                  : 'border-gray-300 hover:border-primary hover:bg-primary/5'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                id="file-upload"
                onChange={handleFileInputChange}
                className="hidden"
                accept=".pdf,.dwg,.dxf,.jpg,.jpeg,.png"
              />

              {!selectedFile ? (
                <div className="space-y-4">
                  <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                    <UploadIcon className="w-8 h-8 text-primary" />
                  </div>
                  <div>
                    <p className="text-lg font-medium text-text mb-2">
                      Glissez-déposez votre fichier ici
                    </p>
                    <p className="text-text/60 text-sm mb-4">
                      ou cliquez pour parcourir vos fichiers
                    </p>
                    <button
                      type="button"
                      onClick={openFileDialog}
                      className="inline-flex items-center space-x-2 px-6 py-3 bg-primary hover:bg-primary-dark text-white font-semibold rounded-lg transition-colors duration-200"
                    >
                      <File className="w-4 h-4" />
                      <span>Choisir un fichier</span>
                    </button>
                  </div>
                  <p className="text-xs text-text/50">
                    Taille maximale: 50MB
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                    <CheckCircle2 className="w-8 h-8 text-green-600" />
                  </div>
                  <div>
                    <p className="text-lg font-medium text-green-700 mb-1">
                      Fichier sélectionné avec succès
                    </p>
                    <p className="text-sm text-text/70">
                      Prêt à être envoyé
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Informations du fichier sélectionné */}
          {selectedFile && (
            <div className="mb-8 p-4 bg-gray-50 rounded-xl border border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <File className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-text">{selectedFile.name}</p>
                    <p className="text-sm text-text/60">
                      {formatFileSize(selectedFile.size)} • {selectedFile.type || 'Type inconnu'}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={removeFile}
                  className="p-2 hover:bg-red-100 rounded-full transition-colors duration-200"
                  title="Supprimer le fichier"
                >
                  <X className="w-5 h-5 text-red-500" />
                </button>
              </div>
            </div>
          )}

          {/* Section des actions */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              type="button"
              onClick={openFileDialog}
              className="flex-1 sm:flex-none px-6 py-3 border-2 border-primary text-primary hover:bg-primary hover:text-white font-semibold rounded-lg transition-all duration-200"
            >
              {selectedFile ? 'Changer le fichier' : 'Parcourir'}
            </button>
            
            <button
              type="submit"
              disabled={!selectedFile}
              className={`flex-1 sm:flex-none px-8 py-3 font-semibold rounded-lg transition-all duration-200 ${
                selectedFile
                  ? 'bg-accent hover:bg-yellow-600 text-white shadow-lg hover:shadow-xl transform hover:-translate-y-0.5'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Envoyer le document
            </button>
          </div>

          {/* Note informative */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex space-x-3">
              <div className="flex-shrink-0">
                <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="text-sm text-blue-700">
                <p className="font-medium">Information importante</p>
                <p className="mt-1">
                  Assurez-vous que votre document est complet et lisible.
                </p>
              </div>
            </div>
          </div>
        </div>
      </form>

      {/* Lecteur audio de bienvenue */}
      <audio ref={audioRef} src="/audio/bouton-vert.mp3" loop />

      {/* Bouton audio mute/unmute */}
      <div className="fixed bottom-4 right-4 z-50">
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
              // Icône son coupé
              <div className="relative">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
                </svg>
                {/* Ligne de coupure */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-10 h-0.5 bg-white rounded-full rotate-45 shadow-lg"></div>
                </div>
              </div>
            ) : (
              // Icône son activé
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

      {/* Styles CSS pour les animations */}
      <style jsx>{`
        .animation-delay-0 { animation-delay: 0ms; }
        .animation-delay-300 { animation-delay: 300ms; }
        .animation-delay-600 { animation-delay: 600ms; }
      `}</style>
    </div>
  );
};

export default Upload;