# 🚀 ANDP - Système d'Analyse Spatiale Intelligente
## Guide de Déploiement Complet

### ✅ IMPLÉMENTATION TERMINÉE

Le système d'analyse spatiale intelligente ANDF est maintenant **complètement implémenté** et prêt pour l'intégration avec votre frontend React + Leaflet.

## 🎯 FONCTIONNALITÉS IMPLÉMENTÉES

### Analyse Spatiale Intelligente:
- ✅ **Détection automatique de double vente** (chevauchement avec TF existants)
- ✅ **Détection d'occupation illégale** (construction sur domaine public DPL/DPM)
- ✅ **Repérage de zones protégées** (aires de conservation)
- ✅ **Repérage de zones litigieuses** (conflits juridiques)
- ✅ **Système d'alerte intelligent** avec recommandations automatiques

### Workflow Complet:
**Upload PDF/Image** → **OCR** → **Extraction coordonnées** → **Création polygone** → **Vérification ANDF** → **Alertes intelligentes** → **Résultats JSON/GeoJSON**

## 📋 ÉTAPES DE DÉPLOIEMENT

### 1. Installation des dépendances:
```bash
pip install -r requirements.txt
```

### 2. Configuration de la base de données:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Import des couches ANDF:
```bash
python manage.py import_layer
```

### 4. Lancement du serveur:
```bash
python manage.py runserver
```

### 5. Test de l'API:
- **Documentation**: http://localhost:8000/api/docs/
- **Test upload**: http://localhost:8000/api/upload/
- **Santé API**: http://localhost:8000/api/health/

## 🔗 API ENDPOINTS POUR FRONTEND REACT

### Workflow Principal:
- `POST /api/upload/` - Upload et analyse complète
- `GET /api/upload/{id}/status/` - Statut temps réel (polling)
- `GET /api/upload/{id}/result/` - Résultats complets

### GeoJSON pour Cartes Leaflet/Mapbox:
- `GET /api/upload/{id}/geojson/` - Parcelle en GeoJSON
- `GET /api/upload/{id}/conflicts/` - Conflits en GeoJSON
- `GET /api/layers/{layer}/geojson/` - Couches ANDF (parcelles, aif, air_proteges, dpl, dpm, litige)
- `GET /api/comparison/{id}/` - Comparaison ancien/nouveau cadastre

### Gestion et Alertes:
- `GET /api/layers/info/` - Informations couches disponibles
- `GET /api/alerts/` - Tableau de bord des alertes
- `GET /api/health/` - État de l'API

## 🔧 INTÉGRATION FRONTEND REACT + LEAFLET

### Exemple d'utilisation:

```javascript
// 1. Upload d'un document
const formData = new FormData();
formData.append('file', selectedFile);

const uploadResponse = await fetch('/api/upload/', {
  method: 'POST',
  body: formData
});

const { upload_id } = await uploadResponse.json();

// 2. Polling du statut
const pollStatus = async () => {
  const response = await fetch(`/api/upload/${upload_id}/status/`);
  const status = await response.json();
  
  if (status.progress_percentage === 100) {
    // Traitement terminé
    loadResults();
  } else {
    // Continuer le polling
    setTimeout(pollStatus, 2000);
  }
};

// 3. Chargement des résultats sur la carte
const loadResults = async () => {
  // Parcelle analysée
  const parcelResponse = await fetch(`/api/upload/${upload_id}/geojson/`);
  const parcelGeoJSON = await parcelResponse.json();
  
  // Conflits détectés
  const conflictsResponse = await fetch(`/api/upload/${upload_id}/conflicts/`);
  const conflictsGeoJSON = await conflictsResponse.json();
  
  // Parcelles existantes pour comparaison
  const comparisonResponse = await fetch(`/api/comparison/${upload_id}/`);
  const comparisonData = await comparisonResponse.json();
  
  // Ajouter à la carte Leaflet
  L.geoJSON(parcelGeoJSON, {
    style: { color: 'blue', weight: 3 }
  }).addTo(map);
  
  L.geoJSON(conflictsGeoJSON, {
    style: { color: 'red', weight: 2, fillOpacity: 0.3 }
  }).addTo(map);
  
  L.geoJSON(comparisonData.existing_parcels, {
    style: { color: 'gray', weight: 1, fillOpacity: 0.1 }
  }).addTo(map);
};
```

### Chargement des couches ANDF:

```javascript
// Charger les parcelles existantes
const parcellesResponse = await fetch('/api/layers/parcelles/geojson/?limit=500&bbox=400000,700000,450000,750000');
const parcellesGeoJSON = await parcellesResponse.json();

// Charger les aires protégées
const protectedResponse = await fetch('/api/layers/air_proteges/geojson/');
const protectedGeoJSON = await protectedResponse.json();

// Ajouter à la carte avec styles différents
L.geoJSON(parcellesGeoJSON, {
  style: { color: 'green', weight: 1, fillOpacity: 0.1 }
}).addTo(map);

L.geoJSON(protectedGeoJSON, {
  style: { color: 'orange', weight: 2, fillOpacity: 0.2 }
}).addTo(map);
```

## 🚨 SYSTÈME D'ALERTE INTELLIGENT

### Types d'alertes automatiques:

1. **🚨 DOUBLE VENTE** - Chevauchement avec parcelles existantes
2. **⛔ OCCUPATION ILLÉGALE** - Construction sur domaine public
3. **🌿 ZONE PROTÉGÉE** - Empiètement sur aire protégée
4. **⚖️ ZONE LITIGIEUSE** - Conflit juridique en cours
5. **📋 INCOHÉRENCE CADASTRALE** - Problème de numérotation

### Niveaux de sévérité:
- **CRITIQUE** (>50% chevauchement) - Intervention immédiate
- **ÉLEVÉ** (>20% chevauchement) - Vérification approfondie
- **MOYEN** (>5% chevauchement) - Attention requise
- **FAIBLE** (>1% chevauchement) - Surveillance

## 📊 STRUCTURE DES RÉPONSES JSON

### Réponse complète d'analyse:
```json
{
  "upload_id": "uuid",
  "status": "completed",
  "processing_time": 45.2,
  "ocr_result": {
    "coordinates_extracted": 8,
    "coordinates_valid": 8,
    "confidence_score": 0.95
  },
  "parcel": {
    "id": "uuid",
    "area": 1234.56,
    "status": "conflict",
    "geometry": { "type": "Feature", ... }
  },
  "spatial_analysis": {
    "total_conflicts": 2,
    "critical_alerts": [...],
    "warnings": [...],
    "recommendations": [...]
  },
  "conflicts": {
    "type": "FeatureCollection",
    "features": [...]
  },
  "map_endpoints": {
    "parcel_geojson": "/api/upload/{id}/geojson/",
    "conflicts_geojson": "/api/upload/{id}/conflicts/",
    "comparison": "/api/comparison/{id}/"
  }
}
```

## 🗂️ FICHIERS CRÉÉS/MODIFIÉS

### Nouveaux fichiers:
- `ANDP_app/services/andf_layers.py` - Gestion couches PostGIS
- `ANDP_app/services/spatial_verification.py` - Analyseur spatial intelligent
- `ANDP_app/services/ocr_integration.py` - Intégration OCR + Spatial
- `ANDP_app/serializers.py` - Serializers pour API REST

### Fichiers modifiés:
- `ANDP_app/models.py` - Ajout modèles vérification spatiale
- `ANDP_app/views.py` - API REST complète
- `ANDP_app/urls.py` - Configuration endpoints
- `ANDP/settings.py` - Configuration CORS + REST Framework
- `requirements.txt` - Dépendances supplémentaires

## ✨ PRÊT POUR PRODUCTION

Le système est maintenant **opérationnel** et prêt à être intégré avec votre frontend React + Tailwind + Leaflet/Mapbox.

### Fonctionnalités clés pour les utilisateurs:
1. **Citoyens/Investisseurs**: Upload de documents → Analyse automatique → Alertes visuelles
2. **Agents ANDF**: Tableau de bord des conflits → Recommandations → Validation

### Avantages du système:
- **Détection automatique** des conflits fonciers
- **Alertes intelligentes** avec recommandations
- **Visualisation interactive** sur carte
- **Comparaison** ancien vs nouveau cadastre
- **API optimisée** pour React + Leaflet

**Le système d'alerte intelligent ANDF est opérationnel ! 🎉**
