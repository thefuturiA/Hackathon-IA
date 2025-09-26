#!/usr/bin/env python3
"""
EXTRACTEUR BASÉ SUR LA LOCALISATION SPATIALE
Stratégie: Le tableau de coordonnées est TOUJOURS dans le coin gauche
Approche: Découper l'image en zones et cibler spécifiquement cette zone
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

class SpatialZoneExtractor(HybridOCRCorrector):
    """
    Extracteur basé sur la LOCALISATION SPATIALE DYNAMIQUE
    
    STRATÉGIE AMÉLIORÉE:
    1. DÉTECTION AUTOMATIQUE des tableaux avec cv2.findContours
    2. LOCALISATION DYNAMIQUE peu importe l'orientation du scan
    3. Fallback sur zones prédéfinies si détection échoue
    4. OCR intensif sur les zones détectées
    """
    
    def extract_coordinates_spatial_zones(self, img_path: str) -> List[Dict]:
        """Extraction basée sur les zones spatiales avec détection dynamique"""
        
        print(f"🗺️  EXTRACTION PAR ZONES SPATIALES DYNAMIQUES pour {os.path.basename(img_path)}")
        print("="*60)
        print("💡 STRATÉGIE AMÉLIORÉE: Détection automatique des tableaux")
        
        # Charger et analyser l'image
        img = cv2.imread(img_path)
        if img is None:
            print("❌ Impossible de charger l'image")
            return []
        
        height, width = img.shape[:2]
        print(f"📐 Dimensions image: {width}x{height}")
        
        # ÉTAPE 1: Détection dynamique des tableaux
        dynamic_zones = self._detect_table_zones_dynamically(img)
        
        # ÉTAPE 2: Zones de fallback si détection échoue
        fallback_zones = self._define_fallback_spatial_zones(width, height)
        
        # Combiner les zones détectées et de fallback
        all_zones = {**dynamic_zones, **fallback_zones}
        
        # Extraire de chaque zone
        all_coordinates = []
        for zone_name, zone_coords in all_zones.items():
            coords = self._extract_from_zone(img, zone_name, zone_coords, img_path)
            all_coordinates.extend(coords)
        
        # Déduplication finale
        final_coords = self._deduplicate_spatial_results(all_coordinates)
        
        return final_coords
    
    def _detect_table_zones_dynamically(self, img: np.ndarray) -> Dict[str, Tuple[int, int, int, int]]:
        """
        DÉTECTION DYNAMIQUE DES TABLEAUX
        Utilise cv2.findContours et pytesseract.image_to_data pour localiser automatiquement
        """
        
        print(f"\n🔍 DÉTECTION DYNAMIQUE DES TABLEAUX:")
        
        dynamic_zones = {}
        height, width = img.shape[:2]
        
        try:
            # Méthode 1: Détection par contours (structures rectangulaires)
            table_zones_contours = self._detect_tables_by_contours(img)
            dynamic_zones.update(table_zones_contours)
            
            # Méthode 2: Détection par analyse OCR (zones avec beaucoup de chiffres)
            table_zones_ocr = self._detect_tables_by_ocr_analysis(img)
            dynamic_zones.update(table_zones_ocr)
            
            # Méthode 3: Détection par densité de texte
            table_zones_density = self._detect_tables_by_text_density(img)
            dynamic_zones.update(table_zones_density)
            
            print(f"   ✅ Zones dynamiques détectées: {len(dynamic_zones)}")
            for zone_name, (x, y, w, h) in dynamic_zones.items():
                print(f"      {zone_name}: ({x},{y}) -> ({w},{h}) [{w-x}x{h-y}]")
                
        except Exception as e:
            print(f"   ❌ Détection dynamique échouée: {e}")
        
        return dynamic_zones
    
    def _detect_tables_by_contours(self, img: np.ndarray) -> Dict[str, Tuple[int, int, int, int]]:
        """Détection des tableaux par analyse des contours"""
        
        zones = {}
        height, width = img.shape[:2]
        
        try:
            # Préprocessing pour la détection de contours
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            
            # Binarisation pour faire ressortir les structures
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # Détection des contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Analyser les contours pour trouver des rectangles de tableau
            table_candidates = []
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Critères pour identifier un tableau:
                # 1. Assez grand (au moins 5% de l'image)
                # 2. Ratio largeur/hauteur raisonnable (pas trop étroit)
                # 3. Pas trop près des bords (marge de sécurité)
                min_area = (width * height) * 0.05
                max_area = (width * height) * 0.8
                
                if (min_area <= area <= max_area and 
                    0.3 <= w/h <= 4.0 and  # Ratio raisonnable
                    x > 10 and y > 10 and  # Pas collé aux bords
                    x + w < width - 10 and y + h < height - 10):
                    
                    table_candidates.append({
                        'zone': (x, y, x+w, y+h),
                        'area': area,
                        'ratio': w/h,
                        'position': 'left' if x < width/2 else 'right'
                    })
            
            # Trier par aire et prendre les meilleurs candidats
            table_candidates.sort(key=lambda t: t['area'], reverse=True)
            
            for i, candidate in enumerate(table_candidates[:3]):  # Max 3 zones
                zone_name = f"contour_table_{i+1}_{candidate['position']}"
                zones[zone_name] = candidate['zone']
                
            print(f"      Contours: {len(zones)} zones détectées")
            
        except Exception as e:
            print(f"      ❌ Détection par contours échouée: {e}")
        
        return zones
    
    def _detect_tables_by_ocr_analysis(self, img: np.ndarray) -> Dict[str, Tuple[int, int, int, int]]:
        """Détection des tableaux par analyse OCR (zones riches en chiffres)"""
        
        zones = {}
        height, width = img.shape[:2]
        
        try:
            # Utiliser pytesseract.image_to_data pour obtenir les positions des mots
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            
            # OCR avec données de position
            ocr_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            # Analyser les zones riches en chiffres (coordonnées)
            digit_zones = []
            
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                conf = int(ocr_data['conf'][i])
                
                # Chercher les textes qui ressemblent à des coordonnées
                if (conf > 30 and len(text) >= 6 and 
                    re.search(r'\d{6,7}', text)):  # Au moins 6 chiffres consécutifs
                    
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    digit_zones.append({
                        'x': x, 'y': y, 'w': w, 'h': h,
                        'text': text, 'conf': conf
                    })
            
            # Grouper les zones proches pour former des régions de tableau
            if digit_zones:
                # Calculer la zone englobante des coordonnées détectées
                min_x = min(zone['x'] for zone in digit_zones)
                min_y = min(zone['y'] for zone in digit_zones)
                max_x = max(zone['x'] + zone['w'] for zone in digit_zones)
                max_y = max(zone['y'] + zone['h'] for zone in digit_zones)
                
                # Ajouter une marge autour de la zone détectée
                margin = 50
                table_x = max(0, min_x - margin)
                table_y = max(0, min_y - margin)
                table_w = min(width, max_x + margin)
                table_h = min(height, max_y + margin)
                
                zones['ocr_digit_zone'] = (table_x, table_y, table_w, table_h)
                
                print(f"      OCR: 1 zone détectée avec {len(digit_zones)} éléments numériques")
            
        except Exception as e:
            print(f"      ❌ Détection par OCR échouée: {e}")
        
        return zones
    
    def _detect_tables_by_text_density(self, img: np.ndarray) -> Dict[str, Tuple[int, int, int, int]]:
        """Détection des tableaux par analyse de la densité de texte"""
        
        zones = {}
        height, width = img.shape[:2]
        
        try:
            # Diviser l'image en grille pour analyser la densité
            grid_rows, grid_cols = 8, 8
            cell_h = height // grid_rows
            cell_w = width // grid_cols
            
            density_map = []
            
            for row in range(grid_rows):
                density_row = []
                for col in range(grid_cols):
                    # Extraire la cellule
                    y1 = row * cell_h
                    y2 = min((row + 1) * cell_h, height)
                    x1 = col * cell_w
                    x2 = min((col + 1) * cell_w, width)
                    
                    cell = img[y1:y2, x1:x2]
                    
                    # Calculer la densité de texte (approximation par variance)
                    gray_cell = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY) if len(cell.shape) == 3 else cell
                    density = np.var(gray_cell)  # Variance comme mesure de complexité
                    
                    density_row.append(density)
                
                density_map.append(density_row)
            
            # Trouver les régions de haute densité
            density_array = np.array(density_map)
            threshold = np.percentile(density_array, 75)  # Top 25% des densités
            
            # Identifier les zones de haute densité
            high_density_regions = []
            for row in range(grid_rows):
                for col in range(grid_cols):
                    if density_array[row, col] > threshold:
                        x1 = col * cell_w
                        y1 = row * cell_h
                        x2 = min((col + 1) * cell_w, width)
                        y2 = min((row + 1) * cell_h, height)
                        
                        high_density_regions.append((x1, y1, x2, y2))
            
            # Fusionner les régions adjacentes
            if high_density_regions:
                # Prendre la région englobante des zones de haute densité
                min_x = min(region[0] for region in high_density_regions)
                min_y = min(region[1] for region in high_density_regions)
                max_x = max(region[2] for region in high_density_regions)
                max_y = max(region[3] for region in high_density_regions)
                
                zones['density_zone'] = (min_x, min_y, max_x, max_y)
                
                print(f"      Densité: 1 zone détectée à partir de {len(high_density_regions)} cellules")
            
        except Exception as e:
            print(f"      ❌ Détection par densité échouée: {e}")
        
        return zones
    
    def _define_fallback_spatial_zones(self, width: int, height: int) -> Dict[str, Tuple[int, int, int, int]]:
        """Définit les zones spatiales de fallback basées sur l'observation"""
        
        zones = {}
        
        print(f"\n🔄 ZONES DE FALLBACK (si détection dynamique échoue):")
        
        # Zone 1: COIN GAUCHE (zone principale du tableau)
        # Observation: Le tableau est SOUVENT dans le coin gauche
        left_width = int(width * 0.4)  # 40% de la largeur
        left_height = int(height * 0.6)  # 60% de la hauteur
        zones['fallback_tableau_principal'] = (0, 0, left_width, left_height)
        
        # Zone 2: GAUCHE ÉTENDU (au cas où le tableau déborde)
        extended_width = int(width * 0.5)  # 50% de la largeur
        zones['fallback_gauche_etendu'] = (0, 0, extended_width, height)
        
        # Zone 3: PARTIE HAUTE GAUCHE (titre et en-têtes)
        top_height = int(height * 0.3)  # 30% de la hauteur
        zones['fallback_titre_gauche'] = (0, 0, left_width, top_height)
        
        # Zone 4: PARTIE BASSE GAUCHE (fin du tableau)
        bottom_start = int(height * 0.4)  # Commence à 40% de la hauteur
        zones['fallback_bas_gauche'] = (0, bottom_start, left_width, height)
        
        print(f"   Zones de fallback définies: {len(zones)}")
        for zone_name, (x, y, w, h) in zones.items():
            print(f"      {zone_name}: ({x},{y}) -> ({w},{h}) [{w-x}x{h-y}]")
        
        return zones
    
    def _extract_from_zone(self, img: np.ndarray, zone_name: str, zone_coords: Tuple[int, int, int, int], img_path: str) -> List[Dict]:
        """Extrait les coordonnées d'une zone spécifique"""
        
        x1, y1, x2, y2 = zone_coords
        zone_img = img[y1:y2, x1:x2]
        
        print(f"\n🔍 EXTRACTION ZONE: {zone_name}")
        print(f"   Dimensions zone: {x2-x1}x{y2-y1}")
        
        # Sauvegarder la zone pour debug
        zone_filename = f"zone_{zone_name}_{os.path.basename(img_path)}"
        cv2.imwrite(zone_filename, zone_img)
        print(f"   💾 Zone sauvée: {zone_filename}")
        
        # OCR intensif sur cette zone
        coordinates = self._intensive_ocr_on_zone(zone_img, zone_name)
        
        print(f"   📍 Coordonnées trouvées: {len(coordinates)}")
        for coord in coordinates:
            print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
        
        return coordinates
    
    def _intensive_ocr_on_zone(self, zone_img: np.ndarray, zone_name: str) -> List[Dict]:
        """OCR intensif sur une zone spécifique"""
        
        coordinates = []
        
        # Préprocessing spécialisé pour les tableaux
        processed_images = self._preprocess_for_table(zone_img)
        
        # OCR avec différentes techniques
        for img_name, processed_img in processed_images:
            
            # PaddleOCR sur la zone
            try:
                # Sauvegarder temporairement pour PaddleOCR
                temp_filename = f"temp_{zone_name}_{img_name}.png"
                cv2.imwrite(temp_filename, processed_img)
                
                ocr_result = self.ocr.ocr(temp_filename)
                if ocr_result and ocr_result[0]:
                    paddle_text = " ".join([line[1][0] for line in ocr_result[0]])
                    corrected_text = self.correct_text_ml(paddle_text)
                    corrected_text = self.apply_borne_corrections(corrected_text)
                    
                    coords = self._extract_coordinates_from_text(corrected_text, f"PaddleOCR_{zone_name}_{img_name}")
                    coordinates.extend(coords)
                
                # Nettoyer le fichier temporaire
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                    
            except Exception as e:
                print(f"      ❌ PaddleOCR {img_name} échoué: {e}")
            
            # Tesseract sur la zone
            for psm in [6, 8, 11, 12]:
                try:
                    config = f"--psm {psm} -c tessedit_char_whitelist=0123456789.,B "
                    text = pytesseract.image_to_string(processed_img, config=config)
                    if text.strip():
                        corrected_text = self.correct_text_ml(text)
                        corrected_text = self.apply_borne_corrections(corrected_text)
                        
                        coords = self._extract_coordinates_from_text(corrected_text, f"Tesseract_{zone_name}_{img_name}_PSM{psm}")
                        coordinates.extend(coords)
                        
                except Exception as e:
                    continue
        
        return coordinates
    
    def _preprocess_for_table(self, zone_img: np.ndarray) -> List[Tuple[str, np.ndarray]]:
        """Préprocessing spécialisé pour les tableaux de coordonnées"""
        
        processed = []
        
        # Image originale
        processed.append(("original", zone_img))
        
        # Conversion en niveaux de gris
        if len(zone_img.shape) == 3:
            gray = cv2.cvtColor(zone_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = zone_img
        processed.append(("gray", gray))
        
        # Amélioration du contraste spécifique aux tableaux
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        processed.append(("enhanced", enhanced))
        
        # Binarisation adaptative (idéale pour les tableaux)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        processed.append(("binary", binary))
        
        # Binarisation OTSU
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed.append(("otsu", otsu))
        
        # Morphologie pour nettoyer les lignes de tableau
        kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        
        # Supprimer les lignes horizontales
        no_horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_horizontal)
        processed.append(("no_horizontal", no_horizontal))
        
        # Supprimer les lignes verticales
        no_vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_vertical)
        processed.append(("no_vertical", no_vertical))
        
        # Dilatation pour épaissir le texte
        kernel_dilate = np.ones((2,2), np.uint8)
        dilated = cv2.dilate(binary, kernel_dilate, iterations=1)
        processed.append(("dilated", dilated))
        
        return processed
    
    def _extract_coordinates_from_text(self, text: str, source: str) -> List[Dict]:
        """Extrait les coordonnées du texte avec patterns spécialisés"""
        
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
        
        # Pattern 3: Format tableau (lignes avec B et coordonnées)
        pattern3 = r'(B\d+).*?(\d{6,7}[.,]?\d{0,3}).*?(\d{6,7}[.,]?\d{0,3})'
        for match in re.finditer(pattern3, text, re.IGNORECASE):
            coord = self._create_coordinate_dict(match, source, 'table', 0.8)
            if coord:
                coordinates.append(coord)
        
        return coordinates
    
    def _create_coordinate_dict(self, match, source: str, pattern_type: str, confidence: float) -> Dict:
        """Crée un dictionnaire de coordonnées à partir d'un match regex"""
        
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
    
    def _deduplicate_spatial_results(self, coordinates: List[Dict]) -> List[Dict]:
        """Déduplication finale des résultats spatiaux avec filtrage intelligent"""
        
        print(f"\n🔍 DÉDUPLICATION SPATIALE INTELLIGENTE:")
        print(f"   Coordonnées brutes: {len(coordinates)}")
        
        if not coordinates:
            return []
        
        # ÉTAPE 1: Filtrer les bornes aberrantes
        valid_coords = []
        for coord in coordinates:
            borne = coord['borne']
            
            # Extraire le numéro de borne
            borne_match = re.match(r'B(\d+)', borne)
            if not borne_match:
                print(f"   ❌ Borne invalide ignorée: {borne}")
                continue
            
            borne_num = int(borne_match.group(1))
            
            # Filtrer les bornes aberrantes (garder seulement B1-B20)
            if borne_num < 1 or borne_num > 20:
                print(f"   ❌ Borne aberrante ignorée: {borne} (numéro {borne_num})")
                continue
            
            # Vérifier que les coordonnées sont dans les bornes UTM du Bénin
            if not self.validate_coordinates(coord['x'], coord['y']):
                print(f"   ❌ Coordonnées hors bornes UTM ignorées: {borne} X={coord['x']:.2f}, Y={coord['y']:.2f}")
                continue
            
            valid_coords.append(coord)
        
        print(f"   Après filtrage: {len(valid_coords)} coordonnées valides")
        
        # ÉTAPE 2: Grouper par borne et déduplication intelligente
        borne_groups = {}
        for coord in valid_coords:
            borne = coord['borne']
            if borne not in borne_groups:
                borne_groups[borne] = []
            borne_groups[borne].append(coord)
        
        # ÉTAPE 3: Sélectionner la meilleure coordonnée pour chaque borne
        final_coords = []
        for borne, coords in borne_groups.items():
            if len(coords) == 1:
                best = coords[0]
            else:
                # Déduplication avancée pour les coordonnées multiples
                best = self._select_best_coordinate_advanced(coords)
            
            final_coords.append(best)
            print(f"   ✅ {borne}: X={best['x']:.2f}, Y={best['y']:.2f} ({best['source'][:30]}...)")
        
        # ÉTAPE 4: Trier par numéro de borne
        final_coords.sort(key=lambda c: int(re.match(r'B(\d+)', c['borne']).group(1)))
        
        print(f"   📍 Coordonnées finales déduplicées: {len(final_coords)}")
        
        return final_coords
    
    def _select_best_coordinate_advanced(self, coords: List[Dict]) -> Dict:
        """Sélection avancée de la meilleure coordonnée parmi les duplicatas"""
        
        if len(coords) == 1:
            return coords[0]
        
        print(f"      🔍 Déduplication de {len(coords)} candidats pour {coords[0]['borne']}")
        
        # Critères de sélection (par ordre de priorité)
        scored_coords = []
        
        for coord in coords:
            score = 0
            
            # 1. Confiance de base
            score += coord.get('confidence', 0) * 100
            
            # 2. Privilégier les sources fiables
            source = coord['source'].lower()
            if 'paddleocr' in source:
                score += 50  # PaddleOCR généralement plus fiable
            if 'tableau_principal' in source or 'fallback_tableau_principal' in source:
                score += 30  # Zone principale privilégiée
            if 'original' in source:
                score += 20  # Image originale privilégiée
            
            # 3. Pénaliser les sources suspectes
            if any(suspect in source for suspect in ['enhanced', 'binary', 'dilated']):
                score -= 10  # Images trop transformées moins fiables
            
            # 4. Vérifier la cohérence des coordonnées
            x, y = coord['x'], coord['y']
            if 350000 <= x <= 450000 and 650000 <= y <= 750000:  # Zone typique du Bénin
                score += 25
            
            scored_coords.append((score, coord))
            print(f"         {coord['borne']}: score={score:.1f} X={x:.2f} Y={y:.2f} ({source[:20]}...)")
        
        # Sélectionner le meilleur score
        scored_coords.sort(key=lambda x: x[0], reverse=True)
        best_coord = scored_coords[0][1]
        
        print(f"      ✅ Meilleur: score={scored_coords[0][0]:.1f}")
        
        return best_coord

def test_spatial_zone_extractor():
    """Test de l'extracteur par zones spatiales avec détection dynamique"""
    
    print("🗺️  TEST EXTRACTEUR PAR ZONES SPATIALES DYNAMIQUES")
    print("="*60)
    print("💡 NOUVELLE STRATÉGIE: Détection automatique des tableaux")
    print("🔍 Méthodes: cv2.findContours + pytesseract.image_to_data + densité de texte")
    
    extractor = SpatialZoneExtractor()
    
    # Fichiers de test
    test_files = [
        #"Testing Data/leve212.png"
        "Testing Data/leve28.png"
        #"Testing Data/leve297.png",
        #"Testing Data/leve298.png"
    ]
    
    results_summary = []
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            continue
            
        filename = os.path.basename(file_path)
        print(f"\n{'='*60}")
        print(f"🗺️  TEST SPATIAL DYNAMIQUE: {filename}")
        print(f"{'='*60}")
        
        try:
            coords = extractor.extract_coordinates_spatial_zones(file_path)
            
            print(f"\n🎯 RÉSULTAT SPATIAL DYNAMIQUE {filename}:")
            print(f"   Coordonnées extraites: {len(coords)}")
            
            if coords:
                borne_numbers = []
                for coord in coords:
                    try:
                        num = int(coord['borne'][1:])
                        borne_numbers.append(num)
                    except:
                        continue
                
                borne_numbers.sort()
                completeness = (len(coords)/8)*100
                
                print(f"   Séquence: {[f'B{n}' for n in borne_numbers]}")
                print(f"   Complétude: {completeness:.1f}%")
                
                # Analyser les sources de détection
                sources = {}
                for coord in coords:
                    source_type = coord['source'].split('_')[0] if '_' in coord['source'] else coord['source']
                    sources[source_type] = sources.get(source_type, 0) + 1
                
                print(f"   Sources de détection: {dict(sources)}")
                
                print(f"\n📍 Détail des coordonnées:")
                for coord in coords:
                    confidence_icon = "🔗" if coord.get('confidence', 0) >= 0.9 else "🔍"
                    print(f"      {confidence_icon} {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
                    print(f"         Source: {coord['source']} (conf: {coord.get('confidence', 0):.2f})")
                
                results_summary.append({
                    'file': filename,
                    'coords': len(coords),
                    'completeness': completeness,
                    'sources': sources
                })
            else:
                print("   ❌ Aucune coordonnée extraite")
                results_summary.append({
                    'file': filename,
                    'coords': 0,
                    'completeness': 0,
                    'sources': {}
                })
                
        except Exception as e:
            print(f"❌ Erreur sur {filename}: {e}")
            results_summary.append({
                'file': filename,
                'error': str(e)
            })
    
    # Résumé final
    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ DÉTECTION DYNAMIQUE")
    print(f"{'='*60}")
    
    for result in results_summary:
        if 'error' in result:
            print(f"❌ {result['file']}: ERREUR - {result['error']}")
        else:
            status = "🏆" if result['completeness'] >= 100 else "✅" if result['completeness'] >= 75 else "👍" if result['completeness'] >= 50 else "⚠️"
            print(f"{status} {result['file']}: {result['coords']} coords ({result['completeness']:.1f}%)")
            if result['sources']:
                print(f"      Méthodes efficaces: {list(result['sources'].keys())}")
    
    print(f"\n{'='*60}")
    print(f"💡 AVANTAGES DÉTECTION DYNAMIQUE")
    print(f"{'='*60}")
    print(f"🎯 Détection automatique des tableaux (cv2.findContours)")
    print(f"🔍 Localisation par analyse OCR (pytesseract.image_to_data)")
    print(f"📊 Analyse de densité de texte (grille 8x8)")
    print(f"🔄 Zones de fallback si détection échoue")
    print(f"✅ Adaptation aux différentes orientations de scan")
    print(f"🚀 Robustesse améliorée pour documents variés")
    
    return results_summary

if __name__ == "__main__":
    test_spatial_zone_extractor()
