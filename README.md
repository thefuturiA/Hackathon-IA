# 🌍 Foncier - Hackathon IA

Foncier est une application web innovante conçue pour faciliter la gestion, la vérification et la visualisation des données foncières et topographiques. Développée dans le cadre d'un Hackathon IA, la plateforme intègre un assistant intelligent (Adam) et des outils cartographiques pour simplifier l'accès à l'information parcellaire.

## ✨ Fonctionnalités Principales

*   **🗺️ Carte Interactive** : Visualisez les parcelles et les données foncières grâce à une intégration fluide avec `react-leaflet`.
*   **📂 Dépôt de Plans Topographiques** : Interface intuitive de glisser-déposer pour soumettre des levés topographiques dans divers formats (PDF, DWG, DXF, JPG, PNG).
*   **🤖 Assistant IA "Adam"** : Un assistant virtuel intégré pour guider les utilisateurs, répondre aux questions sur les données foncières et aider à la navigation.
*   **📄 Détails des Parcelles** : Accédez aux informations détaillées de chaque parcelle enregistrée.
*   **📱 Design Réactif** : Interface utilisateur moderne et accessible, développée avec Tailwind CSS pour s'adapter à tous les écrans.

## 🛠️ Stack Technique

Le projet est basé sur des technologies modernes du web :

*   **Frontend Framework** : React 18
*   **Outil de Build** : Vite
*   **Langage** : TypeScript
*   **Routage** : React Router DOM
*   **Cartographie** : Leaflet & React-Leaflet
*   **Style** : Tailwind CSS
*   **Icônes** : Lucide React

## 🚀 Démarrage Rapide

### Prérequis

*   [Node.js](https://nodejs.org/) (version 18+ recommandée)
*   npm (inclus avec Node.js)

### Installation et Exécution Locale

Étant donné que le code source se trouve dans le sous-dossier `frontend`, assurez-vous de vous y déplacer avant de lancer les commandes.

1.  **Cloner le dépôt et accéder au dossier frontend :**
    ```bash
    cd frontend
    ```

2.  **Installer les dépendances :**
    ```bash
    npm install
    ```

3.  **Lancer le serveur de développement :**
    ```bash
    npm run dev
    ```
    L'application sera accessible (généralement sur `http://localhost:5173`).

### Construction pour la Production

Pour créer une version optimisée pour la production :

```bash
cd frontend
npm run build
```
Les fichiers générés se trouveront dans le dossier `frontend/dist`.

## 📁 Structure du Projet

Le projet principal est contenu dans le dossier `frontend/` :

```text
Hackathon-IA/
├── frontend/
│   ├── public/             # Assets statiques (audio, etc.)
│   ├── src/
│   │   ├── assets/         # Images, icônes (SVG)
│   │   ├── components/     # Composants réutilisables (Navbar, Footer, Hero, Card...)
│   │   ├── pages/          # Pages de l'application (Home, Map, Upload, ParcelDetail)
│   │   ├── App.tsx         # Configuration du routage principal
│   │   └── main.tsx        # Point d'entrée React
│   ├── package.json        # Dépendances et scripts npm
│   ├── tailwind.config.js  # Configuration Tailwind CSS
│   └── vite.config.ts      # Configuration Vite
├── vercel.json             # Configuration de déploiement Vercel
└── README.md               # Ce fichier
```

## 🌐 Déploiement

Le projet est configuré pour être déployé facilement sur **Vercel** grâce au fichier `vercel.json` situé à la racine. Lors du déploiement, Vercel utilise le dossier `frontend` comme répertoire de code source et exécute automatiquement les scripts nécessaires.
