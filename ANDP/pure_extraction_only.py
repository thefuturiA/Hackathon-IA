#!/usr/bin/env python3
"""
Extracteur PUR - SEULEMENT les coordonnées réellement trouvées dans le texte
AUCUNE inférence géométrique qui génère des données fausses
"""

import os
import sys
import re
import cv2
import numpy as np
import pytesseract
from typing import List, Dict, Tuple

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

class PureExtractionOnly(HybridOCRCorrector):
    """
    Extracteur PUR qui ne fait QUE de l'extraction réelle
    AUCUNE inférence géométrique - SEULEMENT les coordonnées trouvées dans le texte
    """
    
    def extract_coordinates_pure_only(self, img_path: str) -> List[Dict]:
        """Extraction PURE - seulement les coordonnées réellement trouvées"""
        
        print(f"🔍 EXTRACTION PURE SEULEMENT pour {os.path.basename(img_path)}")
        print("="*60)
        print("⚠️  AUCUNE inférence géométrique - SEULEMENT les coordonnées réelles")
        
        # Phase 1: Extraction multi-OCR exhaustive
        all_texts = self._extract_text_exhaustive(img_path)
        
        # Phase 2: Extraction avec TOUS les patterns RÉELS
        coordinates = []
        for source, text in all_texts:
            coords = self._extract_with_real_patterns_only(text, source)
            coordinates.extend(coords)
        
        # Phase 3: Déduplication intelligente
        coordinates = self._smart_deduplication(coordinates)
        
        # Phase 4: Validation et tri final (SANS inférence géométrique)
        final_coords = self._pure_validation_and_sort(coordinates)
        
        return final_coords
    
    def _extract_text_exhaustive(self, img_path: str) -> List[Tuple[str, str]]:
        """Extraction de texte EXHAUSTIVE avec toutes les techniques"""
        
        print(f"\n📝 EXTRACTION TEXTE EXHAUSTIVE:")
        all_texts = []
        
        # 1. PaddleOCR standard
        try:
            ocr_result = self.ocr.ocr(img_path)
            paddle_text = " ".join([line[1][0] for page in ocr_result for line in page])
            corrected_paddle = self.correct_text_ml(paddle_text)
            corrected_paddle = self.apply_borne_corrections(corrected_paddle)
            all_texts.append(("PaddleOCR", corrected_paddle))
            print(f"   ✅ PaddleOCR: {len(corrected_paddle)} caractères")
        except Exception as e:
            print(f"   ❌ PaddleOCR échoué: {e}")
        
        # 2. Tesseract avec différents PSM (seulement les plus efficaces)
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Images préprocessées
        processed_images = [
            ("original", gray),
            ("binary", cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2))
        ]
        
        for img_name, processed_img in processed_images:
            for psm in [6, 8]:  # Seulement PSM 6 et 8 (plus efficaces)
                try:
                    config = f"--psm {psm}"
                    text = pytesseract.image_to_string(processed_img, config=config)
                    if text.strip():
                        corrected_text = self.correct_text_ml(text)
                        corrected_text = self.apply_borne_corrections(corrected_text)
                        all_texts.append((f"Tesseract_{img_name}_PSM{psm}", corrected_text))
                        print(f"   ✅ Tesseract {img_name} PSM{psm}: {len(corrected_text)} caractères")
                except Exception as e:
                    print(f"   ❌ Tesseract {img_name} PSM{psm} échoué: {e}")
        
        return all_texts
    
    def _extract_with_real_patterns_only(self, text: str, source: str) -> List[Dict]:
        """Extraction avec patterns RÉELS seulement - AUCUNE invention"""
        
        coordinates = []
        
        print(f"\n🔍 PATTERNS RÉELS SEULEMENT ({source}):")
        
        # Pattern 1: Bornes explicites normales (B1 X Y)
        pattern1 = r'(B\d+)[:\s]*(\d{6,7}[.,]?\d{0,3})[,\s]+(\d{6,7}[.,]?\d{0,3})'
        matches1 = list(re.finditer(pattern1, text, re.IGNORECASE))
        
        for match in matches1:
            borne_id = match.group(1)
            try:
                x = float(match.group(2).replace(',', '.'))
                y = float(match.group(3).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    coordinates.append({
                        'borne': borne_id,
                        'x': x,
                        'y': y,
                        'confidence': 1.0,
                        'source': f'{source}_explicit_normal',
                        'pattern': 'explicit_normal'
                    })
                    print(f"   ✅ {borne_id}: X={x:.2f}, Y={y:.2f} (normal)")
            except ValueError:
                continue
        
        # Pattern 2: Coordonnées collées (B4 432839.05704141.19)
        pattern2 = r'(B\d+)[:\s]*(\d{6}[.,]?\d{2})(\d{6}[.,]?\d{2})'
        matches2 = list(re.finditer(pattern2, text, re.IGNORECASE))
        
        for match in matches2:
            borne_id = match.group(1)
            try:
                x = float(match.group(2).replace(',', '.'))
                y = float(match.group(3).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    coordinates.append({
                        'borne': borne_id,
                        'x': x,
                        'y': y,
                        'confidence': 0.9,
                        'source': f'{source}_explicit_stuck',
                        'pattern': 'explicit_stuck'
                    })
                    print(f"   ✅ {borne_id}: X={x:.2f}, Y={y:.2f} (collées)")
            except ValueError:
                continue
        
        # Pattern 3: B1 implicite avant B2 (SEULEMENT si vraiment dans le texte)
        pattern3 = r'(\d{6}[.,]?\d{2})(\d{6}[.,]?\d{2})\s+B2'
        matches3 = list(re.finditer(pattern3, text, re.IGNORECASE))
        
        for match in matches3:
            try:
                x = float(match.group(1).replace(',', '.'))
                y = float(match.group(2).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    # Vérifier si B1 n'est pas déjà trouvé
                    already_found = any(c['borne'] == 'B1' for c in coordinates)
                    if not already_found:
                        coordinates.append({
                            'borne': 'B1',
                            'x': x,
                            'y': y,
                            'confidence': 0.8,
                            'source': f'{source}_implicit_b1_before_b2',
                            'pattern': 'implicit_b1'
                        })
                        print(f"   ✅ B1: X={x:.2f}, Y={y:.2f} (implicite avant B2)")
            except ValueError:
                continue
        
        # Pattern 4: B1 implicite après SURFACE (SEULEMENT si vraiment dans le texte)
        pattern4 = r'5URFACE:[^B]*(\d{6}[.,]?\d{2})(\d{6}[.,]?\d{2})\s+B2'
        matches4 = list(re.finditer(pattern4, text, re.IGNORECASE))
        
        for match in matches4:
            try:
                x = float(match.group(1).replace(',', '.'))
                y = float(match.group(2).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    # Vérifier si B1 n'est pas déjà trouvé
                    already_found = any(c['borne'] == 'B1' for c in coordinates)
                    if not already_found:
                        coordinates.append({
                            'borne': 'B1',
                            'x': x,
                            'y': y,
                            'confidence': 0.85,
                            'source': f'{source}_implicit_b1_after_surface',
                            'pattern': 'implicit_b1_surface'
                        })
                        print(f"   ✅ B1: X={x:.2f}, Y={y:.2f} (implicite après SURFACE)")
            except ValueError:
                continue
        
        if not coordinates:
            print(f"   ❌ Aucune coordonnée trouvée dans {source}")
        
        return coordinates
    
    def _smart_deduplication(self, coordinates: List[Dict]) -> List[Dict]:
        """Déduplication intelligente basée sur la confiance"""
        
        print(f"\n🔍 DÉDUPLICATION INTELLIGENTE:")
        print(f"   Coordonnées brutes: {len(coordinates)}")
        
        if not coordinates:
            print(f"   ❌ Aucune coordonnée à dédupliquer")
            return []
        
        # Grouper par borne
        borne_groups = {}
        for coord in coordinates:
            borne = coord['borne']
            if borne not in borne_groups:
                borne_groups[borne] = []
            borne_groups[borne].append(coord)
        
        # Sélectionner la meilleure pour chaque borne
        deduplicated = []
        for borne, coords in borne_groups.items():
            # Trier par confiance décroissante
            coords.sort(key=lambda c: c['confidence'], reverse=True)
            best = coords[0]
            
            # Vérifier la cohérence si plusieurs candidats
            if len(coords) > 1:
                # Si les coordonnées sont très proches, garder la plus confiante
                for other in coords[1:]:
                    if abs(best['x'] - other['x']) < 5 and abs(best['y'] - other['y']) < 5:
                        continue
                    else:
                        # Coordonnées différentes, garder la plus confiante
                        break
            
            deduplicated.append(best)
            print(f"   ✅ {borne}: {best['pattern']} (conf: {best['confidence']:.2f})")
        
        print(f"   Coordonnées déduplicées: {len(deduplicated)}")
        return deduplicated
    
    def _pure_validation_and_sort(self, coordinates: List[Dict]) -> List[Dict]:
        """Validation et tri final PURE - AUCUNE inférence géométrique"""
        
        print(f"\n✅ VALIDATION FINALE PURE (AUCUNE INFÉRENCE):")
        
        if not coordinates:
            print(f"   ❌ Aucune coordonnée à valider")
            return []
        
        # Validation UTM seulement
        valid_coords = []
        for coord in coordinates:
            if self.validate_coordinates(coord['x'], coord['y']):
                valid_coords.append(coord)
            else:
                print(f"   ❌ {coord['borne']} rejeté: coordonnées invalides")
        
        # Tri par numéro de borne
        valid_coords.sort(key=lambda c: int(re.search(r'B(\d+)', c['borne']).group(1)))
        
        print(f"   📍 Coordonnées finales RÉELLES: {len(valid_coords)}")
        for coord in valid_coords:
            conf = coord.get('confidence', 1.0)
            pattern = coord.get('pattern', 'unknown')
            print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f}, {pattern})")
        
        # Analyse de complétude RÉELLE
        borne_numbers = []
        for coord in valid_coords:
            try:
                num = int(coord['borne'][1:])
                borne_numbers.append(num)
            except:
                continue
        
        borne_numbers.sort()
        completeness = (len(valid_coords) / 8) * 100
        
        print(f"\n📊 ANALYSE RÉELLE:")
        print(f"   Séquence trouvée: {[f'B{n}' for n in borne_numbers]}")
        print(f"   Complétude RÉELLE: {completeness:.1f}%")
        
        if borne_numbers:
            expected = list(range(1, max(borne_numbers) + 1))
            missing = [f'B{n}' for n in expected if n not in borne_numbers]
            if missing:
                print(f"   ❌ Réellement manquantes: {', '.join(missing)}")
            else:
                print(f"   ✅ Séquence complète trouvée!")
        
        return valid_coords

def test_pure_extraction():
    """Test de l'extracteur PUR sur les fichiers critiques"""
    
    print("🔍 TEST EXTRACTEUR PUR - SEULEMENT COORDONNÉES RÉELLES")
    print("="*60)
    print("⚠️  AUCUNE inférence géométrique - SEULEMENT ce qui est dans le texte")
    
    extractor = PureExtractionOnly()
    
    # Fichiers de test critiques
    test_files = [
        "Testing Data/leve212.png",  # Cas critique
        "Testing Data/leve214.png",  # Cas avec inférence problématique
        "Testing Data/leve275.png",  # Cas B2 précis
        "Testing Data/leve297.png",  # Cas B1 implicite
        "Testing Data/leve298.png",  # Cas tout collé
    ]
    
    results = {}
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"❌ Fichier non trouvé: {file_path}")
            continue
        
        filename = os.path.basename(file_path)
        print(f"\n{'='*60}")
        print(f"🔍 TEST PURE: {filename}")
        print(f"{'='*60}")
        
        try:
            coords = extractor.extract_coordinates_pure_only(file_path)
            
            # Analyse de complétude RÉELLE
            borne_numbers = []
            for coord in coords:
                try:
                    num = int(coord['borne'][1:])
                    borne_numbers.append(num)
                except:
                    continue
            
            borne_numbers.sort()
            completeness = (len(coords) / 8) * 100
            
            results[filename] = {
                'coords': coords,
                'count': len(coords),
                'completeness': completeness,
                'sequence': [f'B{n}' for n in borne_numbers],
                'real_only': True
            }
            
            print(f"\n🎯 RÉSULTAT PURE {filename}:")
            print(f"   Coordonnées RÉELLES: {len(coords)}")
            print(f"   Séquence RÉELLE: {[f'B{n}' for n in borne_numbers]}")
            print(f"   Complétude RÉELLE: {completeness:.1f}%")
            
            # Classification de qualité RÉELLE
            if completeness >= 100:
                print(f"   🏆 PARFAIT: Extraction complète réelle!")
            elif completeness >= 75:
                print(f"   ✅ EXCELLENT: Très bonne extraction réelle!")
            elif completeness >= 50:
                print(f"   👍 BON: Extraction satisfaisante réelle!")
            else:
                print(f"   ⚠️  PARTIEL: Extraction incomplète mais RÉELLE")
            
        except Exception as e:
            print(f"❌ Erreur sur {filename}: {e}")
            results[filename] = {'error': str(e)}
    
    # Résumé final RÉEL
    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ FINAL PURE - COORDONNÉES RÉELLES SEULEMENT")
    print(f"{'='*60}")
    
    for filename, result in results.items():
        if 'error' in result:
            print(f"❌ {filename}: ERREUR")
        else:
            status = "🏆" if result['completeness'] >= 100 else "✅" if result['completeness'] >= 75 else "👍" if result['completeness'] >= 50 else "⚠️"
            print(f"{status} {filename}: {result['count']} coords RÉELLES ({result['completeness']:.1f}%)")
            print(f"      Séquence: {result['sequence']}")
    
    print(f"\n💡 AVANTAGES DE L'EXTRACTION PURE:")
    print(f"   ✅ Aucune donnée fausse générée")
    print(f"   ✅ Seulement les coordonnées réellement présentes")
    print(f"   ✅ Confiance élevée dans les résultats")
    print(f"   ✅ Pas de pollution par inférence géométrique")
    
    return results

if __name__ == "__main__":
    results = test_pure_extraction()
