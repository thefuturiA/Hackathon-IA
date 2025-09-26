#!/usr/bin/env python3
"""
EXTRACTEUR SIMPLE ET ROBUSTE
Implémente les améliorations suggérées une par une, doucement
"""

import os
import sys
import cv2
import numpy as np
import pytesseract
import re
import json
from typing import List, Dict, Tuple, Optional

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

class SimpleRobustExtractor(HybridOCRCorrector):
    """
    Extracteur SIMPLE et ROBUSTE
    Implémente les améliorations suggérées progressivement
    """
    
    def __init__(self):
        super().__init__()
        # Bornes UTM du Bénin (validation stricte)
        self.BENIN_UTM_BOUNDS = {
            'X_MIN': 200000, 'X_MAX': 500000,
            'Y_MIN': 600000, 'Y_MAX': 1400000
        }
    
    def extract_coordinates_simple_robust(self, img_path: str) -> Dict:
        """
        Extraction SIMPLE et ROBUSTE
        Retourne un dictionnaire complet avec métadonnées
        """
        
        print(f"🔍 EXTRACTION SIMPLE ET ROBUSTE")
        print(f"📁 Fichier: {os.path.basename(img_path)}")
        print("="*50)
        
        result = {
            'file': os.path.basename(img_path),
            'coordinates': [],
            'metadata': {},
            'geojson': None,
            'errors': []
        }
        
        try:
            # Étape 1: Détection dynamique de la zone du tableau
            table_zone = self._detect_table_zone_dynamically(img_path)
            result['metadata']['table_zone'] = table_zone
            
            # Étape 2: OCR multilingue sur la zone détectée
            coordinates = self._extract_with_multilingual_ocr(img_path, table_zone)
            
            # Étape 3: Normalisation et validation UTM stricte
            validated_coords = self._normalize_and_validate_utm(coordinates)
            result['coordinates'] = validated_coords
            
            # Étape 4: Export GeoJSON
            if validated_coords:
                geojson = self._export_to_geojson(validated_coords)
                result['geojson'] = geojson
            
            # Métadonnées finales
            result['metadata'].update({
                'count': len(validated_coords),
                'completeness': (len(validated_coords) / 8) * 100,
                'sequence': [c['borne'] for c in validated_coords]
            })
            
        except Exception as e:
            error_msg = f"Erreur extraction: {str(e)}"
            result['errors'].append(error_msg)
            print(f"❌ {error_msg}")
        
        return result
    
    def _detect_table_zone_dynamically(self, img_path: str) -> Optional[Tuple[int, int, int, int]]:
        """
        AMÉLIORATION 1: Détection dynamique de la zone du tableau
        Utilise cv2.findContours pour localiser automatiquement
        """
        
        print("\n🔍 DÉTECTION DYNAMIQUE DE LA ZONE TABLEAU:")
        
        try:
            # Charger l'image
            img = cv2.imread(img_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # Détection des contours pour trouver les tableaux
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Chercher les rectangles qui pourraient être des tableaux
            table_candidates = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Critères pour un tableau:
                # - Assez grand (au moins 10% de l'image)
                # - Ratio largeur/hauteur raisonnable
                # - Situé dans la partie gauche
                if (area > (width * height * 0.1) and 
                    0.5 < w/h < 3.0 and 
                    x < width * 0.6):  # Dans les 60% gauche
                    
                    table_candidates.append((x, y, x+w, y+h, area))
            
            if table_candidates:
                # Prendre le plus grand candidat
                best_table = max(table_candidates, key=lambda t: t[4])
                zone = best_table[:4]
                print(f"   ✅ Zone tableau détectée: ({zone[0]},{zone[1]}) -> ({zone[2]},{zone[3]})")
                return zone
            else:
                # Fallback: zone gauche par défaut
                fallback_zone = (0, 0, int(width * 0.4), int(height * 0.6))
                print(f"   ⚠️  Fallback zone gauche: {fallback_zone}")
                return fallback_zone
                
        except Exception as e:
            print(f"   ❌ Détection échouée: {e}")
            # Fallback sécurisé
            return (0, 0, 300, 400)
    
    def _extract_with_multilingual_ocr(self, img_path: str, table_zone: Tuple[int, int, int, int]) -> List[Dict]:
        """
        AMÉLIORATION 2: OCR multilingue (français + anglais)
        Configure Tesseract avec lang='fra+eng'
        """
        
        print(f"\n🌍 OCR MULTILINGUE (français + anglais):")
        
        coordinates = []
        
        # Extraire la zone du tableau
        img = cv2.imread(img_path)
        x1, y1, x2, y2 = table_zone
        table_img = img[y1:y2, x1:x2]
        
        # Préprocessing simple
        gray = cv2.cvtColor(table_img, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # OCR multilingue avec Tesseract
        try:
            # Configuration multilingue
            config = "--psm 6 -l fra+eng"
            text = pytesseract.image_to_string(binary, config=config)
            
            if text.strip():
                print(f"   ✅ Texte extrait ({len(text)} caractères)")
                print(f"   📝 Aperçu: {text[:100]}...")
                
                # Correction et extraction
                corrected_text = self.correct_text_ml(text)
                corrected_text = self.apply_borne_corrections(corrected_text)
                
                coords = self._extract_coordinates_from_text(corrected_text)
                coordinates.extend(coords)
                
                print(f"   📍 Coordonnées brutes: {len(coords)}")
            else:
                print(f"   ❌ Aucun texte extrait")
                
        except Exception as e:
            print(f"   ❌ OCR multilingue échoué: {e}")
        
        # Fallback avec PaddleOCR
        try:
            temp_filename = "temp_table_zone.png"
            cv2.imwrite(temp_filename, table_img)
            
            ocr_result = self.ocr.ocr(temp_filename)
            if ocr_result and ocr_result[0]:
                paddle_text = " ".join([line[1][0] for line in ocr_result[0]])
                corrected_text = self.correct_text_ml(paddle_text)
                corrected_text = self.apply_borne_corrections(corrected_text)
                
                coords = self._extract_coordinates_from_text(corrected_text)
                coordinates.extend(coords)
                
                print(f"   ✅ PaddleOCR: {len(coords)} coordonnées")
            
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                
        except Exception as e:
            print(f"   ❌ PaddleOCR échoué: {e}")
        
        return coordinates
    
    def _extract_coordinates_from_text(self, text: str) -> List[Dict]:
        """Extraction simple avec patterns de base"""
        
        coordinates = []
        
        # Pattern simple: B1 X Y
        pattern = r'(B\d+)[:\s]*(\d{6,7}[.,]?\d{0,3})[,\s]+(\d{6,7}[.,]?\d{0,3})'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                borne_id = match.group(1)
                x = float(match.group(2).replace(',', '.'))
                y = float(match.group(3).replace(',', '.'))
                
                coordinates.append({
                    'borne': borne_id,
                    'x': x,
                    'y': y,
                    'raw': True
                })
                
            except ValueError:
                continue
        
        return coordinates
    
    def _normalize_and_validate_utm(self, coordinates: List[Dict]) -> List[Dict]:
        """
        AMÉLIORATION 3: Normalisation et validation UTM stricte
        Filtre les faux positifs avec les bornes UTM du Bénin
        """
        
        print(f"\n✅ NORMALISATION ET VALIDATION UTM:")
        print(f"   Coordonnées brutes: {len(coordinates)}")
        
        validated = []
        
        for coord in coordinates:
            x, y = coord['x'], coord['y']
            
            # Validation UTM Bénin stricte
            if (self.BENIN_UTM_BOUNDS['X_MIN'] <= x <= self.BENIN_UTM_BOUNDS['X_MAX'] and
                self.BENIN_UTM_BOUNDS['Y_MIN'] <= y <= self.BENIN_UTM_BOUNDS['Y_MAX']):
                
                validated.append({
                    'borne': coord['borne'],
                    'x': x,
                    'y': y,
                    'utm_valid': True
                })
                print(f"   ✅ {coord['borne']}: X={x:.2f}, Y={y:.2f} (UTM valide)")
            else:
                print(f"   ❌ {coord['borne']}: X={x:.2f}, Y={y:.2f} (hors bornes UTM)")
        
        print(f"   📍 Coordonnées UTM validées: {len(validated)}")
        
        # Déduplication simple
        seen_bornes = set()
        final_coords = []
        for coord in validated:
            if coord['borne'] not in seen_bornes:
                seen_bornes.add(coord['borne'])
                final_coords.append(coord)
        
        # Tri par numéro de borne
        final_coords.sort(key=lambda c: int(re.search(r'B(\d+)', c['borne']).group(1)))
        
        return final_coords
    
    def _export_to_geojson(self, coordinates: List[Dict]) -> Dict:
        """
        AMÉLIORATION 4: Export direct en GeoJSON
        Format standard pour Leaflet, PostGIS, QGIS
        """
        
        print(f"\n🗺️  EXPORT GEOJSON:")
        
        if len(coordinates) < 3:
            print(f"   ❌ Pas assez de coordonnées pour un polygone ({len(coordinates)} < 3)")
            return None
        
        # Créer les coordonnées du polygone
        polygon_coords = []
        for coord in coordinates:
            # GeoJSON utilise [longitude, latitude] mais nous avons [X, Y] UTM
            # Pour le Bénin, on garde X, Y tel quel
            polygon_coords.append([coord['x'], coord['y']])
        
        # Fermer le polygone (retour au premier point)
        if polygon_coords[0] != polygon_coords[-1]:
            polygon_coords.append(polygon_coords[0])
        
        # Structure GeoJSON
        geojson = {
            "type": "Feature",
            "properties": {
                "name": f"Levé topographique",
                "bornes": [c['borne'] for c in coordinates],
                "count": len(coordinates),
                "utm_zone": "31N",
                "country": "Bénin"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [polygon_coords]
            }
        }
        
        print(f"   ✅ GeoJSON créé: {len(coordinates)} points")
        print(f"   📐 Polygone: {len(polygon_coords)} coordonnées")
        
        return geojson

def test_simple_robust_one_by_one():
    """Test simple et robuste, un fichier à la fois"""
    
    print("🔍 TEST SIMPLE ET ROBUSTE - UN PAR UN")
    print("="*50)
    
    extractor = SimpleRobustExtractor()
    
    # Test sur UN SEUL fichier d'abord
    test_file = "Testing Data/leve212.png"
    
    if not os.path.exists(test_file):
        print(f"❌ Fichier non trouvé: {test_file}")
        return
    
    print(f"🎯 TEST SUR: {os.path.basename(test_file)}")
    print("="*50)
    
    try:
        result = extractor.extract_coordinates_simple_robust(test_file)
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   Fichier: {result['file']}")
        print(f"   Coordonnées: {result['metadata']['count']}")
        print(f"   Complétude: {result['metadata']['completeness']:.1f}%")
        print(f"   Séquence: {result['metadata']['sequence']}")
        
        if result['coordinates']:
            print(f"\n📍 COORDONNÉES VALIDÉES:")
            for coord in result['coordinates']:
                print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
        
        if result['geojson']:
            print(f"\n🗺️  GEOJSON GÉNÉRÉ:")
            print(f"   Type: {result['geojson']['geometry']['type']}")
            print(f"   Points: {len(result['geojson']['geometry']['coordinates'][0])}")
            
            # Sauvegarder le GeoJSON
            geojson_filename = f"{result['file']}.geojson"
            with open(geojson_filename, 'w', encoding='utf-8') as f:
                json.dump(result['geojson'], f, indent=2, ensure_ascii=False)
            print(f"   💾 Sauvé: {geojson_filename}")
        
        if result['errors']:
            print(f"\n❌ ERREURS:")
            for error in result['errors']:
                print(f"   - {error}")
        
        print(f"\n✅ Test terminé pour {result['file']}")
        return result
        
    except Exception as e:
        print(f"❌ Erreur globale: {e}")
        return None

def test_multiple_files_carefully():
    """Test sur plusieurs fichiers, doucement"""
    
    print("\n" + "="*50)
    print("🔍 TEST MULTIPLE - DOUCEMENT")
    print("="*50)
    
    extractor = SimpleRobustExtractor()
    
    # Fichiers de test (commencer petit)
    test_files = [
        "Testing Data/leve212.png"
    ]
    
    results = []
    
    for i, file_path in enumerate(test_files, 1):
        if not os.path.exists(file_path):
            continue
        
        print(f"\n[{i}/{len(test_files)}] 🔍 Test: {os.path.basename(file_path)}")
        print("-" * 30)
        
        try:
            result = extractor.extract_coordinates_simple_robust(file_path)
            results.append(result)
            
            # Résumé rapide
            count = result['metadata']['count']
            completeness = result['metadata']['completeness']
            status = "✅" if count >= 4 else "⚠️" if count >= 2 else "❌"
            
            print(f"   {status} {count} coords ({completeness:.1f}%)")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    # Résumé final
    print(f"\n" + "="*50)
    print(f"📊 RÉSUMÉ FINAL")
    print("="*50)
    
    for result in results:
        if result:
            count = result['metadata']['count']
            completeness = result['metadata']['completeness']
            status = "✅" if completeness >= 50 else "⚠️" if completeness >= 25 else "❌"
            print(f"{status} {result['file']}: {count} coords ({completeness:.1f}%)")
    
    return results

if __name__ == "__main__":
    # Test simple d'abord
    single_result = test_simple_robust_one_by_one()
    
    # Si ça marche, test multiple
    if single_result and single_result['metadata']['count'] > 0:
        print(f"\n🚀 Test simple réussi, continuons avec plusieurs fichiers...")
        multiple_results = test_multiple_files_carefully()
    else:
        print(f"\n⚠️  Test simple échoué, arrêt ici")
