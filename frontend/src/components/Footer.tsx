import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-primary-dark text-white p-6 mt-8">
      <div className="container mx-auto flex flex-col md:flex-row justify-between items-center text-sm">
        <div className="mb-4 md:mb-0 text-center md:text-left">
          <p>&copy; {new Date().getFullYear()} ANDF. Tous droits réservés.</p>
          <p>Contact : andf@finances.bj</p>
        </div>
        <div className="text-center md:text-right">
          <a href=":/https://andf.bj/" target="_blank" rel="noopener noreferrer" className="hover:underline text-accent">
            Agence Nationale du Domaine et du Foncier (ANDF)
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;