import React from 'react';

interface CardProps {
  icon: string;
  title: string;
  description: string;
}

const Card: React.FC<CardProps> = ({ icon, title, description }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 flex flex-col items-center text-center hover:shadow-lg transition-shadow duration-300">

      <img src={icon} alt={title} className="w-16 h-16 mb-4 text-primary" />
      <h3 className="text-xl font-semibold text-primary-dark mb-3">{title}</h3>
      <p className="text-text text-sm">{description}</p>
    </div>
  );
};

export default Card;