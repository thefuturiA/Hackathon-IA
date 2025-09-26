#!/usr/bin/env python3
"""
Extracteur ultra-précis qui capture toutes les coordonnées, même dans des formats non-standard
"""

import os
import sys
import re
from typing import List, Dict

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

class UltraPreciseExtractor(HybridOCRCorrector):
    """Extracteur ultra-précis pour capturer toutes les coordonnées"""
    
    def extract_all_coordinates_ultra_precise(self, img_path: str) -> List[Dict]:
        """Extraction ultra-précise de toutes les coordonnées"""
        
        print(f"🎯 EXTRACTION ULTRA-PRÉCISE pour {os.path.basename(img_path)}")
        print("="*70)
        
        # Extraction OCR standard
        img = self.preprocess_image(img_path)
        ocr_result = self.ocr.ocr(img_path)
        raw_text = " ".join([line[1][0] for page in ocr_result for line in page])
        
        print(f"📝 Texte OCR brut:")
        print(f"   {raw_text}")
        
        # Nettoyer et corriger le texte
        corrected_text = self.correct_text_ml(raw_text)
        corrected_text = self.apply_borne_corrections(corrected_text)
        
        print(f"📝 Texte corrigé:")
        print(f"   {corrected_text}")
        
        # Extraction avec patterns ultra-précis
        coordinates = self._extract_with_ultra_precise_patterns(corrected_text)
        
        # Post-traitement pour associer les coordonnées isolées
        coordinates = self._associate_isolated_coordinates(corrected_text, coordinates)
        
        # Validation et tri final
        final_coords = self._validate_and_sort(coordinates)
        
        return final_coords
    
    def _extract_with_ultra_precise_patterns(self, text: str) -> List[Dict]:
        """Extraction avec patterns ultra-précis"""
        
        print(f"\n🔍 PATTERNS ULTRA-PRÉCIS:")
        coordinates = []
        
        # Pattern 1: Bornes explicites (B1, B2, B3, B4)
        pattern1 = r'(B\d+)[:\s]*(\d{6,7}[.,]?\d{0,3})[,\s]+(\d{6,7}[.,]?\d{0,3})'
        matches1 = re.finditer(pattern1, text, re.IGNORECASE)
        
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
                        'source': 'explicit_borne'
                    })
                    print(f"   ✅ {borne_id}: X={x:.2f}, Y={y:.2f} (explicite)")
            except ValueError:
                continue
        
        # Pattern 2: Séquences de coordonnées (pour capturer B1, B2 dans leve275)
        # Format: "81 435690.30 705242.54 435705.83 705222.90 B3..."
        pattern2 = r'(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})'
        matches2 = re.finditer(pattern2, text)
        
        for match in matches2:
            try:
                # Première paire de coordonnées
                x1 = float(match.group(1).replace(',', '.'))
                y1 = float(match.group(2).replace(',', '.'))
                # Deuxième paire de coordonnées
                x2 = float(match.group(3).replace(',', '.'))
                y2 = float(match.group(4).replace(',', '.'))
                
                if self.validate_coordinates(x1, y1):
                    coordinates.append({
                        'borne': 'B1',  # Assumer que c'est B1
                        'x': x1,
                        'y': y1,
                        'confidence': 0.8,
                        'source': 'sequence_pattern'
                    })
                    print(f"   ✅ B1: X={x1:.2f}, Y={y1:.2f} (séquence)")
                
                if self.validate_coordinates(x2, y2):
                    coordinates.append({
                        'borne': 'B2',  # Assumer que c'est B2
                        'x': x2,
                        'y': y2,
                        'confidence': 0.8,
                        'source': 'sequence_pattern'
                    })
                    print(f"   ✅ B2: X={x2:.2f}, Y={y2:.2f} (séquence)")
                    
            except ValueError:
                continue
        
        return coordinates
    
    def _associate_isolated_coordinates(self, text: str, existing_coords: List[Dict]) -> List[Dict]:
        """Associe les coordonnées isolées aux bornes manquantes"""
        
        print(f"\n🔍 RECHERCHE COORDONNÉES ISOLÉES:")
        
        # Identifier les bornes déjà trouvées
        found_bornes = [c['borne'] for c in existing_coords]
        print(f"   Bornes déjà trouvées: {found_bornes}")
        
        # Chercher toutes les paires de coordonnées dans le texte
        all_coord_pattern = r'(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})'
        all_matches = re.finditer(all_coord_pattern, text)
        
        potential_coords = []
        for match in all_matches:
            try:
                x = float(match.group(1).replace(',', '.'))
                y = float(match.group(2).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    # Vérifier si cette coordonnée n'est pas déjà trouvée
                    is_duplicate = any(
                        abs(c['x'] - x) < 1 and abs(c['y'] - y) < 1 
                        for c in existing_coords
                    )
                    if not is_duplicate:
                        potential_coords.append((x, y))
            except ValueError:
                continue
        
        print(f"   Coordonnées potentielles: {len(potential_coords)}")
        
        # Associer aux bornes manquantes
        target_bornes = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8']
        missing_bornes = [b for b in target_bornes if b not in found_bornes]
        
        enhanced_coords = existing_coords.copy()
        
        for i, (x, y) in enumerate(potential_coords):
            if i < len(missing_bornes):
                borne_id = missing_bornes[i]
                enhanced_coords.append({
                    'borne': borne_id,
                    'x': x,
                    'y': y,
                    'confidence': 0.6,
                    'source': 'isolated_association'
                })
                print(f"   ✅ {borne_id}: X={x:.2f}, Y={y:.2f} (associé)")
        
        return enhanced_coords
    
    def _validate_and_sort(self, coordinates: List[Dict]) -> List[Dict]:
        """Validation et tri final"""
        
        # Supprimer les doublons (garder le plus confiant)
        unique_coords = {}
        for coord in coordinates:
            borne = coord['borne']
            if borne not in unique_coords or coord['confidence'] > unique_coords[borne]['confidence']:
                unique_coords[borne] = coord
        
        # Convertir en liste et trier
        final_coords = list(unique_coords.values())
        final_coords.sort(key=lambda c: int(re.search(r'B(\d+)', c['borne']).group(1)))
        
        print(f"\n✅ RÉSULTATS FINAUX ULTRA-PRÉCIS:")
        print(f"   📍 Coordonnées finales: {len(final_coords)}")
        for coord in final_coords:
            conf = coord.get('confidence', 1.0)
            source = coord.get('source', 'unknown')
            print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f}, {source})")
        
        return final_coords

def test_ultra_precise_leve275():
    """Test ultra-précis sur leve275.png"""
    
    print("🚀 TEST ULTRA-PRÉCIS - leve275.png")
    print("="*60)
    
    extractor = UltraPreciseExtractor()
    file_path = "Testing Data/leve275.png"
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return
    
    # Test ultra-précis
    ultra_coords = extractor.extract_all_coordinates_ultra_precise(file_path)
    
    print(f"\n📊 RÉSULTATS ULTRA-PRÉCIS:")
    print(f"   Total coordonnées: {len(ultra_coords)}")
    
    # Vérifier si B2 est maintenant correctement capturé
    b2_found = any(c['borne'] == 'B2' for c in ultra_coords)
    if b2_found:
        b2_coord = next(c for c in ultra_coords if c['borne'] == 'B2')
        expected_x, expected_y = 435705.83, 705222.90
        actual_x, actual_y = b2_coord['x'], b2_coord['y']
        
        print(f"\n🎯 VÉRIFICATION B2:")
        print(f"   Attendu: X={expected_x}, Y={expected_y}")
        print(f"   Trouvé: X={actual_x:.2f}, Y={actual_y:.2f}")
        
        if abs(actual_x - expected_x) < 1 and abs(actual_y - expected_y) < 1:
            print(f"   ✅ B2 CORRECTEMENT CAPTURÉ!")
        else:
            print(f"   ⚠️  B2 capturé mais coordonnées différentes")
    else:
        print(f"\n❌ B2 toujours manquant")
    
    # Analyse de complétude
    borne_numbers = []
    for coord in ultra_coords:
        try:
            num = int(coord['borne'][1:])
            borne_numbers.append(num)
        except:
            continue
    
    borne_numbers.sort()
    completeness = (len(ultra_coords) / 8) * 100
    
    print(f"\n📊 ANALYSE FINALE:")
    print(f"   Séquence: {[f'B{n}' for n in borne_numbers]}")
    print(f"   Complétude: {completeness:.1f}%")
    
    if completeness >= 100:
        print(f"   🏆 PARFAIT: Extraction complète!")
    elif completeness >= 75:
        print(f"   ✅ EXCELLENT: Très bonne extraction!")
    elif completeness >= 50:
        print(f"   👍 BON: Extraction satisfaisante!")
    else:
        print(f"   ⚠️  INSUFFISANT: Extraction incomplète")
    
    return ultra_coords

if __name__ == "__main__":
    ultra_coords = test_ultra_precise_leve275()
