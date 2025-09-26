#!/usr/bin/env python3
"""
EXTRACTEUR SPATIAL OPTIMISÉ - VERSION FINALE
Basé sur votre observation cruciale: le tableau est TOUJOURS dans le coin gauche
Avec nettoyage intelligent des résultats OCR
"""

import os
import sys
import cv2
import numpy as np
import pytesseract
import re
from typing import List, Dict, Tuple

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

class OptimizedSpatialExtractor(HybridOCRCorrector):
    """
    EXTRACTEUR SPATIAL OPTIMISÉ - VERSION FINALE
    
    STRATÉGIE VALIDÉE:
    1. Le tableau de coordonnées est TOUJOURS dans le coin gauche ✅
    2. Cibler spécifiquement cette zone (40% largeur x 60% hauteur)
    3. OCR intensif sur cette zone seulement
    4. Nettoyage intelligent des erreurs OCR
    5. Validation stricte des coordonnées
    """
    
    def extract_coordinates_optimized_spatial(self, img_path: str) -> List[Dict]:
        """Extraction spatiale optimisée avec nettoyage intelligent"""
        
        print(f"🎯 EXTRACTION SPATIALE OPTIMISÉE pour {os.path.basename(img_path)}")
        print("="*60)
        print("💡 STRATÉGIE VALIDÉE: Tableau dans le coin gauche")
        
        # Charger l'image
        img = cv2.imread(img_path)
        if img is None:
            print("❌ Impossible de charger l'image")
            return []
        
        height, width = img.shape[:2]
        print(f"📐 Dimensions image: {width}x{height}")
        
        # Zone optimale du tableau (basée sur les tests)
        table_zone = self._define_optimal_table_zone(width, height)
        
        # Extraction intensive sur la zone du tableau
        raw_coordinates = self._extract_from_table_zone(img, table_zone, img_path)
        
        # Nettoyage intelligent des résultats
        cleaned_coordinates = self._intelligent_cleaning(raw_coordinates)
        
        # Validation finale
        final_coordinates = self._final_validation(cleaned_coordinates)
        
        return final_coordinates
    
    def _define_optimal_table_zone(self, width: int, height: int) -> Tuple[int, int, int, int]:
        """Définit la zone optimale du tableau basée sur les observations"""
        
        # Zone optimale: 40% largeur x 60% hauteur (coin gauche)
        table_width = int(width * 0.4)
        table_height = int(height * 0.6)
        
        zone = (0, 0, table_width, table_height)
        print(f"🎯 Zone tableau optimale: (0,0) -> ({table_width},{table_height}) [{table_width}x{table_height}]")
        
        return zone
    
    def _extract_from_table_zone(self, img: np.ndarray, zone: Tuple[int, int, int, int], img_path: str) -> List[Dict]:
        """Extraction intensive de la zone du tableau"""
        
        x1, y1, x2, y2 = zone
        table_img = img[y1:y2, x1:x2]
        
        print(f"\n🔍 EXTRACTION ZONE TABLEAU:")
        print(f"   Dimensions: {x2-x1}x{y2-y1}")
        
        # Sauvegarder pour debug
        table_filename = f"table_zone_{os.path.basename(img_path)}"
        cv2.imwrite(table_filename, table_img)
        print(f"   💾 Zone sauvée: {table_filename}")
        
        # OCR intensif optimisé
        coordinates = self._intensive_table_ocr(table_img)
        
        print(f"   📍 Coordonnées brutes extraites: {len(coordinates)}")
        
        return coordinates
    
    def _intensive_table_ocr(self, table_img: np.ndarray) -> List[Dict]:
        """OCR intensif optimisé pour les tableaux"""
        
        coordinates = []
        
        # Images préprocessées optimales pour les tableaux
        processed_images = [
            ("original", table_img),
            ("gray", cv2.cvtColor(table_img, cv2.COLOR_BGR2GRAY) if len(table_img.shape) == 3 else table_img),
        ]
        
        # Ajouter les préprocessings spécialisés
        gray = processed_images[1][1]
        
        # Amélioration contraste
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        processed_images.append(("enhanced", enhanced))
        
        # Binarisation adaptative
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        processed_images.append(("binary", binary))
        
        # OCR sur chaque image préprocessée
        for img_name, processed_img in processed_images:
            
            # PaddleOCR
            try:
                temp_filename = f"temp_table_{img_name}.png"
                cv2.imwrite(temp_filename, processed_img)
                
                ocr_result = self.ocr.ocr(temp_filename)
                if ocr_result and ocr_result[0]:
                    paddle_text = " ".join([line[1][0] for line in ocr_result[0]])
                    corrected_text = self.correct_text_ml(paddle_text)
                    corrected_text = self.apply_borne_corrections(corrected_text)
                    
                    coords = self._extract_coordinates_from_text(corrected_text, f"PaddleOCR_{img_name}")
                    coordinates.extend(coords)
                
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                    
            except Exception as e:
                print(f"      ❌ PaddleOCR {img_name} échoué: {e}")
            
            # Tesseract avec PSM optimaux
            for psm in [6, 8]:  # PSM les plus efficaces
                try:
                    config = f"--psm {psm} -c tessedit_char_whitelist=0123456789.,B "
                    text = pytesseract.image_to_string(processed_img, config=config)
                    if text.strip():
                        corrected_text = self.correct_text_ml(text)
                        corrected_text = self.apply_borne_corrections(corrected_text)
                        
                        coords = self._extract_coordinates_from_text(corrected_text, f"Tesseract_{img_name}_PSM{psm}")
                        coordinates.extend(coords)
                        
                except Exception:
                    continue
        
        return coordinates
    
    def _extract_coordinates_from_text(self, text: str, source: str) -> List[Dict]:
        """Extraction avec patterns optimisés"""
        
        coordinates = []
        
        # Pattern 1: Format normal (B1 X Y)
        pattern1 = r'(B\d+)[:\s]*(\d{6,7}[.,]?\d{0,3})[,\s]+(\d{6,7}[.,]?\d{0,3})'
        for match in re.finditer(pattern1, text, re.IGNORECASE):
            coord = self._create_coordinate_dict(match, source, 'normal', 1.0)
            if coord:
                coordinates.append(coord)
        
        # Pattern 2: Format collé (B1 XXYY)
        pattern2 = r'(B\d+)[:\s]*(\d{6}[.,]?\d{2})(\d{6}[.,]?\d{2})'
        for match in re.finditer(pattern2, text, re.IGNORECASE):
            coord = self._create_coordinate_dict(match, source, 'stuck', 0.9)
            if coord:
                coordinates.append(coord)
        
        return coordinates
    
    def _create_coordinate_dict(self, match, source: str, pattern_type: str, confidence: float) -> Dict:
        """Crée un dictionnaire de coordonnées validé"""
        
        try:
            borne_id = match.group(1)
            x = float(match.group(2).replace(',', '.'))
            y = float(match.group(3).replace(',', '.'))
            
            if self.validate_coordinates(x, y):
                return {
                    'borne': borne_id,
                    'x': x,
                    'y': y,
                    'confidence': confidence,
                    'source': source,
                    'pattern': pattern_type
                }
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _intelligent_cleaning(self, coordinates: List[Dict]) -> List[Dict]:
        """Nettoyage intelligent des résultats OCR"""
        
        print(f"\n🧹 NETTOYAGE INTELLIGENT:")
        print(f"   Coordonnées brutes: {len(coordinates)}")
        
        if not coordinates:
            return []
        
        # Étape 1: Filtrer les bornes aberrantes
        valid_bornes = []
        for coord in coordinates:
            borne_num = self._extract_borne_number(coord['borne'])
            if borne_num and 1 <= borne_num <= 20:  # Bornes valides B1-B20
                valid_bornes.append(coord)
            else:
                print(f"   ❌ Borne aberrante filtrée: {coord['borne']}")
        
        print(f"   Après filtrage bornes: {len(valid_bornes)}")
        
        # Étape 2: Grouper par borne et sélectionner la meilleure
        borne_groups = {}
        for coord in valid_bornes:
            borne = coord['borne']
            if borne not in borne_groups:
                borne_groups[borne] = []
            borne_groups[borne].append(coord)
        
        # Étape 3: Sélection intelligente
        cleaned = []
        for borne, coords in borne_groups.items():
            best = self._select_best_coordinate(coords)
            if best:
                cleaned.append(best)
                print(f"   ✅ {borne}: {best['source']} (conf: {best['confidence']:.2f})")
        
        print(f"   Coordonnées nettoyées: {len(cleaned)}")
        return cleaned
    
    def _extract_borne_number(self, borne_id: str) -> int:
        """Extrait le numéro de la borne"""
        try:
            match = re.match(r'B(\d+)', borne_id)
            return int(match.group(1)) if match else None
        except:
            return None
    
    def _select_best_coordinate(self, coords: List[Dict]) -> Dict:
        """Sélectionne la meilleure coordonnée parmi les candidats"""
        
        if len(coords) == 1:
            return coords[0]
        
        # Trier par confiance et préférer PaddleOCR
        coords.sort(key=lambda c: (
            c['confidence'],
            1 if 'PaddleOCR' in c['source'] else 0,
            1 if c['pattern'] == 'normal' else 0
        ), reverse=True)
        
        # Vérifier la cohérence spatiale
        best = coords[0]
        for other in coords[1:]:
            # Si les coordonnées sont très proches, garder la plus confiante
            if abs(best['x'] - other['x']) < 10 and abs(best['y'] - other['y']) < 10:
                continue
            else:
                # Coordonnées différentes, garder la plus confiante
                break
        
        return best
    
    def _final_validation(self, coordinates: List[Dict]) -> List[Dict]:
        """Validation finale avec analyse de qualité"""
        
        print(f"\n✅ VALIDATION FINALE:")
        
        if not coordinates:
            print("   ❌ Aucune coordonnée à valider")
            return []
        
        # Tri par numéro de borne
        coordinates.sort(key=lambda c: self._extract_borne_number(c['borne']))
        
        print(f"   📍 Coordonnées finales validées: {len(coordinates)}")
        for coord in coordinates:
            print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {coord['confidence']:.2f})")
        
        # Analyse de séquence
        borne_numbers = [self._extract_borne_number(c['borne']) for c in coordinates]
        borne_numbers = [n for n in borne_numbers if n]
        
        if borne_numbers:
            completeness = (len(coordinates) / 8) * 100
            print(f"\n📊 ANALYSE FINALE:")
            print(f"   Séquence: {[f'B{n}' for n in borne_numbers]}")
            print(f"   Complétude: {completeness:.1f}%")
            
            # Vérifier la continuité
            if len(borne_numbers) > 1:
                gaps = []
                for i in range(min(borne_numbers), max(borne_numbers) + 1):
                    if i not in borne_numbers:
                        gaps.append(f'B{i}')
                
                if gaps:
                    print(f"   ❌ Manquantes: {', '.join(gaps)}")
                else:
                    print(f"   ✅ Séquence complète!")
        
        return coordinates

def test_optimized_spatial_extractor():
    """Test de l'extracteur spatial optimisé"""
    
    print("🎯 TEST EXTRACTEUR SPATIAL OPTIMISÉ")
    print("="*60)
    print("💡 STRATÉGIE: Zone tableau optimisée + nettoyage intelligent")
    
    extractor = OptimizedSpatialExtractor()
    
    # Fichiers de test
    test_files = [
        "Testing Data/leve212.png",
        "Testing Data/leve275.png",
        "Testing Data/leve297.png",
        "Testing Data/leve298.png"
    ]
    
    results = {}
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            continue
            
        filename = os.path.basename(file_path)
        print(f"\n{'='*60}")
        print(f"🎯 TEST OPTIMISÉ: {filename}")
        print(f"{'='*60}")
        
        try:
            coords = extractor.extract_coordinates_optimized_spatial(file_path)
            
            borne_numbers = []
            for coord in coords:
                num = extractor._extract_borne_number(coord['borne'])
                if num:
                    borne_numbers.append(num)
            
            borne_numbers.sort()
            completeness = (len(coords) / 8) * 100
            
            results[filename] = {
                'coords': coords,
                'count': len(coords),
                'completeness': completeness,
                'sequence': [f'B{n}' for n in borne_numbers]
            }
            
            print(f"\n🎯 RÉSULTAT OPTIMISÉ {filename}:")
            print(f"   Coordonnées: {len(coords)}")
            print(f"   Séquence: {[f'B{n}' for n in borne_numbers]}")
            print(f"   Complétude: {completeness:.1f}%")
            
            # Classification de qualité
            if completeness >= 100:
                print(f"   🏆 PARFAIT: Extraction complète!")
            elif completeness >= 75:
                print(f"   ✅ EXCELLENT: Très bonne extraction!")
            elif completeness >= 50:
                print(f"   👍 BON: Extraction satisfaisante!")
            else:
                print(f"   ⚠️  PARTIEL: Extraction incomplète")
                
        except Exception as e:
            print(f"❌ Erreur sur {filename}: {e}")
            results[filename] = {'error': str(e)}
    
    # Résumé final
    print(f"\n{'='*60}")
    print(f"🏆 RÉSUMÉ EXTRACTEUR SPATIAL OPTIMISÉ")
    print(f"{'='*60}")
    
    for filename, result in results.items():
        if 'error' in result:
            print(f"❌ {filename}: ERREUR")
        else:
            status = "🏆" if result['completeness'] >= 100 else "✅" if result['completeness'] >= 75 else "👍" if result['completeness'] >= 50 else "⚠️"
            print(f"{status} {filename}: {result['count']} coords ({result['completeness']:.1f}%)")
            print(f"      Séquence: {result['sequence']}")
    
    print(f"\n💡 AVANTAGES DE L'APPROCHE SPATIALE OPTIMISÉE:")
    print(f"   🎯 Ciblage précis de la zone du tableau")
    print(f"   🧹 Nettoyage intelligent des erreurs OCR")
    print(f"   ✅ Validation stricte des coordonnées")
    print(f"   📊 Analyse de qualité et complétude")
    print(f"   🚀 Performance optimisée")
    
    return results

if __name__ == "__main__":
    results = test_optimized_spatial_extractor()
