import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import LogoSVG from '/logo.svg';

const Navbar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  return (
    <nav className="bg-primary-dark p-4 shadow-md">
      <div className="container mx-auto flex justify-between items-center">
        <NavLink to="/" className="flex items-center">
          <img src={LogoSVG} alt="LE FONCIER INTELLIGENT Logo" className="h-8 mr-3" />
          <span className="text-white text-xl font-semibold">ANDF</span>
        </NavLink>

        <div className="hidden md:flex items-center space-x-6">
          <NavLink to="/" className={({ isActive }) => `text-white hover:text-accent transition-colors duration-200 ${isActive ? 'font-bold text-accent' : ''}`}>
            Accueil
          </NavLink>
          <NavLink to="/map" className={({ isActive }) => `text-white hover:text-accent transition-colors duration-200 ${isActive ? 'font-bold text-accent' : ''}`}>
            Carte
          </NavLink>
          <NavLink to="/upload" className={({ isActive }) => `text-white hover:text-accent transition-colors duration-200 ${isActive ? 'font-bold text-accent' : ''}`}>
            Déposer levé
          </NavLink>
          <NavLink to="/faq" className={({ isActive }) => `text-white hover:text-accent transition-colors duration-200 ${isActive ? 'font-bold text-accent' : ''}`}>
            FAQ
          </NavLink>
          <span className="text-white px-3 py-1 border border-white rounded-full text-xs">FR</span>
        </div>

        <div className="md:hidden flex items-center">
          <span className="text-white mr-3 px-3 py-1 border border-white rounded-full text-xs">FR</span>
          <button onClick={toggleMenu} className="text-white focus:outline-none">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              {isOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path>
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-primary-dark mt-2 pb-2">
          <div className="flex flex-col items-center">
            <NavLink to="/" onClick={toggleMenu} className="block text-white py-2 hover:text-accent transition-colors duration-200">Accueil</NavLink>
            <NavLink to="/map" onClick={toggleMenu} className="block text-white py-2 hover:text-accent transition-colors duration-200">Carte</NavLink>
            <NavLink to="/upload" onClick={toggleMenu} className="block text-white py-2 hover:text-accent transition-colors duration-200">Déposer levé</NavLink>
            <NavLink to="/faq" onClick={toggleMenu} className="block text-white py-2 hover:text-accent transition-colors duration-200">FAQ</NavLink>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;