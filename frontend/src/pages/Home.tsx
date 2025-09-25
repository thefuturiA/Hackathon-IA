import React from 'react';
import Hero from '../components/Hero';
import Card from '../components/Card';
import { ReliabilityIcon, TopographicIcon, InclusionIcon } from '../assets';

const Home: React.FC = () => {
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
    </div>
  );
};

export default Home;