#!/usr/bin/env python3
"""
Extracteur ultra-précis CORRIGÉ qui gère les coordonnées collées comme B4 432839.05704141.19
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

class FixedUltraPreciseExtractor(HybridOCRCorrector):
    """Extracteur ultra-précis CORRIGÉ pour capturer TOUTES les coordonnées"""
    
    def extract_all_coordinates_fixed(self, img_path: str) -> List[Dict]:
        """Extraction ultra-précise CORRIGÉE de toutes les coordonnées"""
        
        print(f"🎯 EXTRACTION ULTRA-PRÉCISE CORRIGÉE pour {os.path.basename(img_path)}")
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
        
        # Extraction avec patterns ultra-précis CORRIGÉS
        coordinates = self._extract_with_fixed_patterns(corrected_text)
        
        # Post-traitement pour associer les coordonnées isolées
        coordinates = self._associate_isolated_coordinates(corrected_text, coordinates)
        
        # Validation et tri final
        final_coords = self._validate_and_sort(coordinates)
        
        return final_coords
    
    def _extract_with_fixed_patterns(self, text: str) -> List[Dict]:
        """Extraction avec patterns CORRIGÉS pour gérer les coordonnées collées"""
        
        print(f"\n🔍 PATTERNS ULTRA-PRÉCIS CORRIGÉS:")
        coordinates = []
        
        # Pattern 1: Bornes explicites normales (B1 X Y)
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
                        'source': 'explicit_borne_normal'
                    })
                    print(f"   ✅ {borne_id}: X={x:.2f}, Y={y:.2f} (normal)")
            except ValueError:
                continue
        
        # Pattern 2: NOUVEAU - Bornes avec coordonnées COLLÉES (B4 432839.05704141.19)
        pattern2 = r'(B\d+)[:\s]*(\d{6}[.,]?\d{2})(\d{6}[.,]?\d{2})'
        matches2 = re.finditer(pattern2, text, re.IGNORECASE)
        
        for match in matches2:
            borne_id = match.group(1)
            try:
                x = float(match.group(2).replace(',', '.'))
                y = float(match.group(3).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    # Vérifier si cette borne n'est pas déjà trouvée
                    already_found = any(c['borne'] == borne_id for c in coordinates)
                    if not already_found:
                        coordinates.append({
                            'borne': borne_id,
                            'x': x,
                            'y': y,
                            'confidence': 0.9,
                            'source': 'explicit_borne_stuck'
                        })
                        print(f"   ✅ {borne_id}: X={x:.2f}, Y={y:.2f} (collées)")
            except ValueError:
                continue
        
        # Pattern 3: Séquences de coordonnées (pour capturer B1, B2 dans certains cas)
        pattern3 = r'(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})'
        matches3 = re.finditer(pattern3, text)
        
        for match in matches3:
            try:
                # Première paire de coordonnées
                x1 = float(match.group(1).replace(',', '.'))
                y1 = float(match.group(2).replace(',', '.'))
                # Deuxième paire de coordonnées
                x2 = float(match.group(3).replace(',', '.'))
                y2 = float(match.group(4).replace(',', '.'))
                
                # Assigner aux bornes manquantes
                found_bornes = [c['borne'] for c in coordinates]
                
                if self.validate_coordinates(x1, y1) and 'B1' not in found_bornes:
                    coordinates.append({
                        'borne': 'B1',
                        'x': x1,
                        'y': y1,
                        'confidence': 0.8,
                        'source': 'sequence_pattern'
                    })
                    print(f"   ✅ B1: X={x1:.2f}, Y={y1:.2f} (séquence)")
                
                if self.validate_coordinates(x2, y2) and 'B2' not in found_bornes:
                    coordinates.append({
                        'borne': 'B2',
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
        
        print(f"\n✅ RÉSULTATS FINAUX ULTRA-PRÉCIS CORRIGÉS:")
        print(f"   📍 Coordonnées finales: {len(final_coords)}")
        for coord in final_coords:
            conf = coord.get('confidence', 1.0)
            source = coord.get('source', 'unknown')
            print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f}, {source})")
        
        return final_coords

def test_fixed_extractor_leve278():
    """Test de l'extracteur CORRIGÉ sur leve278.png"""
    
    print("🚀 TEST EXTRACTEUR ULTRA-PRÉCIS CORRIGÉ - leve29.png")
    print("="*60)
    
    extractor = FixedUltraPreciseExtractor()
    file_path = "Testing Data/leve29.png"
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return
    
    # Test de l'extraction corrigée
    fixed_coords = extractor.extract_all_coordinates_fixed(file_path)
    
    print(f"\n📊 RÉSULTATS FINAUX CORRIGÉS:")
    print(f"   Total coordonnées: {len(fixed_coords)}")
    
    # Vérifier si B4 est maintenant correctement capturé
    b4_found = any(c['borne'] == 'B4' for c in fixed_coords)
    if b4_found:
        b4_coord = next(c for c in fixed_coords if c['borne'] == 'B4')
        print(f"\n🎯 VÉRIFICATION B4:")
        print(f"   ✅ B4 TROUVÉ: X={b4_coord['x']:.2f}, Y={b4_coord['y']:.2f}")
        print(f"   Source: {b4_coord.get('source', 'unknown')}")
        print(f"   Confiance: {b4_coord.get('confidence', 1.0):.2f}")
    else:
        print(f"\n❌ B4 toujours manquant")
    
    # Analyse de complétude
    borne_numbers = []
    for coord in fixed_coords:
        try:
            num = int(coord['borne'][1:])
            borne_numbers.append(num)
        except:
            continue
    
    borne_numbers.sort()
    completeness = (len(fixed_coords) / 8) * 100
    
    print(f"\n📊 ANALYSE FINALE CORRIGÉE:")
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
    
    # Comparaison avec le standard
    print(f"\n📊 COMPARAISON AVEC STANDARD:")
    print(f"   Standard: 4 coordonnées (B1, B2, B3, B4)")
    print(f"   Corrigé: {len(fixed_coords)} coordonnées")
    
    if len(fixed_coords) >= 4:
        print(f"   🎉 SUCCÈS: Égalité ou amélioration!")
    else:
        print(f"   ⚠️  ATTENTION: Encore en dessous du standard")
    
    return fixed_coords

if __name__ == "__main__":
    fixed_coords = test_fixed_extractor_leve278()
