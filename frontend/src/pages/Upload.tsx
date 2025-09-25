import React from 'react';

const Upload: React.FC = () => {
  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-primary-dark mb-6">Déposer votre levé topographique</h1>
      <form className="bg-white p-6 rounded-lg shadow-md">
        <div className="mb-4">
          <label htmlFor="file-upload" className="block text-text text-sm font-bold mb-2">
            Sélectionnez votre document ici depuis votre appareil
          </label>
          <input
            type="file"
            id="file-upload"
            className="block w-full text-sm text-text
                       file:mr-4 file:py-2 file:px-4
                       file:rounded-full file:border-0
                       file:text-sm file:font-semibold
                       file:bg-primary file:text-white
                       hover:file:bg-primary-dark"
          />
        </div>
        <div className="mb-4">
          <label htmlFor="description" className="block text-text text-sm font-bold mb-2">
            Description (optionnel)
          </label>
          <textarea
            id="description"
            rows={4}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-text leading-tight focus:outline-none focus:shadow-outline"
            placeholder="Ajoutez une description de votre levé..."
          ></textarea>
        </div>
        <button
          type="submit"
          className="bg-accent hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
        >
          Envoyer
        </button>
      </form>
    </div>
  );
};

export default Upload;