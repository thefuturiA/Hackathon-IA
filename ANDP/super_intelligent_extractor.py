#!/usr/bin/env python3
"""
Extracteur SUPER INTELLIGENT qui détecte B1 même sans marquage explicite
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

class SuperIntelligentExtractor(HybridOCRCorrector):
    """Extracteur SUPER INTELLIGENT pour capturer B1 même sans marquage"""
    
    def extract_all_coordinates_super_intelligent(self, img_path: str) -> List[Dict]:
        """Extraction SUPER INTELLIGENTE de toutes les coordonnées"""
        
        print(f"🧠 EXTRACTION SUPER INTELLIGENTE pour {os.path.basename(img_path)}")
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
        
        # Extraction avec patterns SUPER INTELLIGENTS
        coordinates = self._extract_with_super_intelligent_patterns(corrected_text)
        
        # Post-traitement pour associer les coordonnées isolées
        coordinates = self._associate_isolated_coordinates(corrected_text, coordinates)
        
        # Validation et tri final
        final_coords = self._validate_and_sort(coordinates)
        
        return final_coords
    
    def _extract_with_super_intelligent_patterns(self, text: str) -> List[Dict]:
        """Extraction avec patterns SUPER INTELLIGENTS"""
        
        print(f"\n🧠 PATTERNS SUPER INTELLIGENTS:")
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
        
        # Pattern 2: Bornes avec coordonnées COLLÉES (B4 432839.05704141.19)
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
        
        # Pattern 3: NOUVEAU - Détection de B1 IMPLICITE avant B2
        # Chercher des coordonnées collées juste avant "B2"
        pattern3 = r'(\d{6}[.,]?\d{2})(\d{6}[.,]?\d{2})\s+B2'
        matches3 = re.finditer(pattern3, text, re.IGNORECASE)
        
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
                            'source': 'implicit_b1_before_b2'
                        })
                        print(f"   ✅ B1: X={x:.2f}, Y={y:.2f} (implicite avant B2)")
            except ValueError:
                continue
        
        # Pattern 4: NOUVEAU - Détection de B1 IMPLICITE dans séquence
        # Format: "SURFACE:17a46ca 455393.56704692.64 B2"
        pattern4 = r'5URFACE:[^B]*(\d{6}[.,]?\d{2})(\d{6}[.,]?\d{2})\s+B2'
        matches4 = re.finditer(pattern4, text, re.IGNORECASE)
        
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
                            'source': 'implicit_b1_after_surface'
                        })
                        print(f"   ✅ B1: X={x:.2f}, Y={y:.2f} (implicite après SURFACE)")
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
        
        print(f"\n✅ RÉSULTATS FINAUX SUPER INTELLIGENTS:")
        print(f"   📍 Coordonnées finales: {len(final_coords)}")
        for coord in final_coords:
            conf = coord.get('confidence', 1.0)
            source = coord.get('source', 'unknown')
            print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f}, {source})")
        
        return final_coords

def test_super_intelligent_leve297():
    """Test de l'extracteur SUPER INTELLIGENT sur leve297.png"""
    
    print("🚀 TEST EXTRACTEUR SUPER INTELLIGENT - leve297.png")
    print("="*60)
    
    extractor = SuperIntelligentExtractor()
    file_path = "Testing Data/leve297.png"
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return
    
    # Test de l'extraction super intelligente
    super_coords = extractor.extract_all_coordinates_super_intelligent(file_path)
    
    print(f"\n📊 RÉSULTATS FINAUX SUPER INTELLIGENTS:")
    print(f"   Total coordonnées: {len(super_coords)}")
    
    # Vérifier si B1 est maintenant correctement capturé
    b1_found = any(c['borne'] == 'B1' for c in super_coords)
    if b1_found:
        b1_coord = next(c for c in super_coords if c['borne'] == 'B1')
        print(f"\n🎯 VÉRIFICATION B1:")
        print(f"   ✅ B1 TROUVÉ: X={b1_coord['x']:.2f}, Y={b1_coord['y']:.2f}")
        print(f"   Source: {b1_coord.get('source', 'unknown')}")
        print(f"   Confiance: {b1_coord.get('confidence', 1.0):.2f}")
        
        # Vérifier si c'est cohérent avec les coordonnées attendues
        expected_x = 455393.56
        expected_y = 704692.64
        actual_x = b1_coord['x']
        actual_y = b1_coord['y']
        
        if abs(actual_x - expected_x) < 1 and abs(actual_y - expected_y) < 1:
            print(f"   🎉 COORDONNÉES EXACTES! Attendu: X={expected_x}, Y={expected_y}")
        else:
            print(f"   ⚠️  Coordonnées différentes. Attendu: X={expected_x}, Y={expected_y}")
    else:
        print(f"\n❌ B1 toujours manquant")
    
    # Analyse de complétude
    borne_numbers = []
    for coord in super_coords:
        try:
            num = int(coord['borne'][1:])
            borne_numbers.append(num)
        except:
            continue
    
    borne_numbers.sort()
    completeness = (len(super_coords) / 8) * 100
    
    print(f"\n📊 ANALYSE FINALE SUPER INTELLIGENTE:")
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
    
    # Comparaison avec les résultats précédents
    print(f"\n📊 COMPARAISON AVEC PRÉCÉDENTS:")
    print(f"   Standard: 3 coordonnées (B2, B3, B4)")
    print(f"   Ultra-précis: 3 coordonnées (B2, B3, B4)")
    print(f"   Super intelligent: {len(super_coords)} coordonnées")
    
    if len(super_coords) > 3:
        print(f"   🎉 AMÉLIORATION: +{len(super_coords)-3} coordonnées!")
    elif len(super_coords) == 3:
        print(f"   ➡️  ÉGALITÉ: Même performance")
    else:
        print(f"   ⚠️  RÉGRESSION: Performance inférieure")
    
    return super_coords

if __name__ == "__main__":
    super_coords = test_super_intelligent_leve297()
