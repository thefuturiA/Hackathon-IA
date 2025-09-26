import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, File, X, CheckCircle2 } from 'lucide-react';

const Upload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    </div>
  );
};

export default Upload;
