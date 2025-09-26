#!/usr/bin/env python3
"""
Debug spécifique pour leve212.png - analyse des coordonnées manquantes
"""

import os
import sys
import cv2
import numpy as np
import re
from PIL import Image
import matplotlib.pyplot as plt

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

def debug_leve212():
    """Debug détaillé pour leve212.png"""
    
    print("🔍 DEBUG SPÉCIFIQUE - leve212.png")
    print("="*50)
    
    file_path = "Testing Data/leve212.png"
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return
    
    # Initialiser l'extracteur
    extractor = HybridOCRCorrector()
    
    print(f"📁 Fichier: {file_path}")
    
    # Charger et analyser l'image
    original_img = cv2.imread(file_path)
    height, width = original_img.shape[:2]
    print(f"📏 Dimensions: {width}x{height} pixels")
    
    # Préprocessing détaillé
    print(f"\n🖼️  PRÉPROCESSING DÉTAILLÉ:")
    
    # Image originale en niveaux de gris
    gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
    print(f"   Conversion en niveaux de gris: {gray.shape}")
    
    # Débruitage
    denoised = cv2.fastNlMeansDenoising(gray)
    print(f"   Débruitage appliqué")
    
    # Amélioration du contraste
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    print(f"   Amélioration du contraste (CLAHE)")
    
    # Binarisation adaptative
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    print(f"   Binarisation adaptative")
    
    # Morphologie
    kernel = np.ones((2,2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    print(f"   Opérations morphologiques")
    
    # Sauvegarder les étapes de préprocessing
    cv2.imwrite("leve212_gray.png", gray)
    cv2.imwrite("leve212_denoised.png", denoised)
    cv2.imwrite("leve212_enhanced.png", enhanced)
    cv2.imwrite("leve212_binary.png", binary)
    cv2.imwrite("leve212_cleaned.png", cleaned)
    print(f"   ✅ Images de debug sauvées")
    
    # OCR avec PaddleOCR
    print(f"\n🔍 EXTRACTION OCR DÉTAILLÉE:")
    
    # Utiliser l'extracteur pour obtenir le texte brut
    ocr_result = extractor.ocr.ocr(file_path)
    raw_texts = []
    
    print(f"   Nombre de pages détectées: {len(ocr_result)}")
    
    for page_idx, page in enumerate(ocr_result):
        print(f"   Page {page_idx + 1}: {len(page)} éléments détectés")
        for line_idx, line in enumerate(page):
            bbox, (text, confidence) = line
            raw_texts.append(text)
            print(f"      {line_idx + 1:2d}. '{text}' (conf: {confidence:.3f})")
    
    # Texte combiné
    combined_text = " ".join(raw_texts)
    print(f"\n📝 TEXTE BRUT COMBINÉ:")
    print(f"   {combined_text[:200]}...")
    
    # Tesseract OCR aussi
    import pytesseract
    tesseract_text = pytesseract.image_to_string(cleaned, config="--psm 6")
    print(f"\n📝 TEXTE TESSERACT:")
    print(f"   {tesseract_text[:200]}...")
    
    # Texte final combiné
    final_text = combined_text + " " + tesseract_text
    
    # Correction ML
    corrected_text = extractor.correct_text_ml(final_text)
    corrected_text = extractor.apply_borne_corrections(corrected_text)
    
    print(f"\n📝 TEXTE CORRIGÉ:")
    print(f"   {corrected_text[:300]}...")
    
    # Analyse des patterns avec tous les patterns possibles
    print(f"\n🔍 ANALYSE DES PATTERNS:")
    
    patterns = [
        (r'(B\d+)(\d{6,7}[.,]?\d{0,3})(\d{6,7}[.,]?\d{0,3})', "Pattern collé"),
        (r'(B\d+)[:\s]*[XxEe]?[:\s]*(\d{6,7}[.,]?\d{0,3})[,\s]+[YyNn]?[:\s]*(\d{6,7}[.,]?\d{0,3})', "Pattern principal"),
        (r'(B\d+)[:\s]+(\d{6,7}[.,]?\d{0,3})[,\s]+(\d{6,7}[.,]?\d{0,3})', "Pattern alternatif"),
        (r'(B\d+)[^\d]*(\d{6,7}[.,]?\d{0,2})[^\d]*(\d{6,7}[.,]?\d{0,2})', "Pattern simple"),
        # Patterns supplémentaires pour capturer plus de cas
        (r'B(\d+)[^\d]*(\d{6,7}[.,]?\d{0,3})[^\d]*(\d{6,7}[.,]?\d{0,3})', "Pattern sans B initial"),
        (r'(\d+)[^\d]*(\d{6,7}[.,]?\d{0,3})[^\d]*(\d{6,7}[.,]?\d{0,3})', "Pattern numérique pur"),
    ]
    
    all_coordinates = []
    
    for pattern, description in patterns:
        matches = list(re.finditer(pattern, corrected_text))
        print(f"   {description}: {len(matches)} correspondances")
        
        for match in matches:
            try:
                if pattern.startswith(r'(B\d+)'):
                    borne_id = match.group(1)
                    x = float(match.group(2).replace(',', '.'))
                    y = float(match.group(3).replace(',', '.'))
                elif pattern.startswith(r'B(\d+)'):
                    borne_id = f"B{match.group(1)}"
                    x = float(match.group(2).replace(',', '.'))
                    y = float(match.group(3).replace(',', '.'))
                else:
                    borne_id = f"B{match.group(1)}"
                    x = float(match.group(2).replace(',', '.'))
                    y = float(match.group(3).replace(',', '.'))
                
                if extractor.validate_coordinates(x, y):
                    coord = {'borne': borne_id, 'x': x, 'y': y, 'pattern': description}
                    # Éviter les doublons
                    if not any(c['borne'] == borne_id for c in all_coordinates):
                        all_coordinates.append(coord)
                        print(f"      ✅ {borne_id}: X={x}, Y={y}")
                    else:
                        print(f"      🔄 {borne_id}: X={x}, Y={y} (doublon)")
                else:
                    print(f"      ❌ {borne_id}: X={x}, Y={y} (invalide)")
                    
            except (ValueError, IndexError) as e:
                print(f"      ⚠️  Erreur parsing: {match.group(0)} - {e}")
    
    # Recherche manuelle de coordonnées dans le texte
    print(f"\n🔍 RECHERCHE MANUELLE DE COORDONNÉES:")
    
    # Chercher tous les nombres qui ressemblent à des coordonnées
    coord_numbers = re.findall(r'\d{6,7}[.,]?\d{0,3}', corrected_text)
    print(f"   Nombres potentiels trouvés: {len(coord_numbers)}")
    
    valid_x_coords = []
    valid_y_coords = []
    
    for num_str in coord_numbers:
        try:
            num = float(num_str.replace(',', '.'))
            if extractor.validate_coordinates(num, 700000):  # Test avec Y arbitraire
                valid_x_coords.append(num)
                print(f"      X potentiel: {num}")
            elif extractor.validate_coordinates(400000, num):  # Test avec X arbitraire
                valid_y_coords.append(num)
                print(f"      Y potentiel: {num}")
        except ValueError:
            continue
    
    print(f"   X valides trouvés: {len(valid_x_coords)}")
    print(f"   Y valides trouvés: {len(valid_y_coords)}")
    
    # Résultats finaux
    print(f"\n📊 RÉSULTATS FINAUX:")
    print(f"   Coordonnées extraites: {len(all_coordinates)}")
    
    if all_coordinates:
        print(f"\n📍 COORDONNÉES TROUVÉES:")
        for i, coord in enumerate(all_coordinates, 1):
            print(f"   {i:2d}. {coord['borne']}: X={coord['x']:>10.2f}, Y={coord['y']:>10.2f} ({coord['pattern']})")
    
    # Créer une visualisation
    create_debug_visualization(file_path, all_coordinates, corrected_text)
    
    return all_coordinates

def create_debug_visualization(image_path, coordinates, extracted_text):
    """Crée une visualisation de debug"""
    
    print(f"\n📈 CRÉATION DE LA VISUALISATION DEBUG...")
    
    # Charger l'image originale
    img = Image.open(image_path)
    
    # Créer la figure avec trois sous-graphiques
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # Graphique 1: Image originale
    ax1.imshow(img)
    ax1.set_title("Image Originale - leve212.png", fontsize=14, fontweight='bold')
    ax1.axis('off')
    
    # Graphique 2: Image préprocessée
    preprocessed = cv2.imread("leve212_cleaned.png", cv2.IMREAD_GRAYSCALE)
    ax2.imshow(preprocessed, cmap='gray')
    ax2.set_title("Image Préprocessée", fontsize=14, fontweight='bold')
    ax2.axis('off')
    
    # Graphique 3: Plan des coordonnées
    if coordinates:
        x_coords = [c['x'] for c in coordinates]
        y_coords = [c['y'] for c in coordinates]
        
        # Tracer les points
        ax3.scatter(x_coords, y_coords, c='red', s=100, zorder=5)
        
        # Tracer les lignes du polygone
        if len(coordinates) >= 3:
            x_poly = x_coords + [x_coords[0]]
            y_poly = y_coords + [y_coords[0]]
            ax3.plot(x_poly, y_poly, 'b-', linewidth=2, alpha=0.7)
            ax3.fill(x_poly, y_poly, alpha=0.2, color='blue')
        
        # Annoter les points
        for coord in coordinates:
            ax3.annotate(coord['borne'], 
                        (coord['x'], coord['y']), 
                        xytext=(5, 5), 
                        textcoords='offset points',
                        fontsize=10, 
                        fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        
        ax3.set_xlabel('X (UTM)', fontsize=12)
        ax3.set_ylabel('Y (UTM)', fontsize=12)
        ax3.set_title('Coordonnées Extraites', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.set_aspect('equal')
        
        # Ajuster les marges
        margin_x = (max(x_coords) - min(x_coords)) * 0.1 if len(x_coords) > 1 else 10
        margin_y = (max(y_coords) - min(y_coords)) * 0.1 if len(y_coords) > 1 else 10
        ax3.set_xlim(min(x_coords) - margin_x, max(x_coords) + margin_x)
        ax3.set_ylim(min(y_coords) - margin_y, max(y_coords) + margin_y)
    else:
        ax3.text(0.5, 0.5, 'Aucune coordonnée extraite', 
                ha='center', va='center', transform=ax3.transAxes,
                fontsize=16, color='red')
        ax3.set_title('Coordonnées Extraites', fontsize=14, fontweight='bold')
    
    # Graphique 4: Texte extrait (tronqué)
    ax4.text(0.05, 0.95, f"Texte extrait (premiers 500 caractères):\n\n{extracted_text[:500]}...", 
            transform=ax4.transAxes, fontsize=8, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8),
            family='monospace')
    ax4.set_title('Texte OCR Extrait', fontsize=14, fontweight='bold')
    ax4.axis('off')
    
    plt.tight_layout()
    
    # Sauvegarder la visualisation
    output_file = "leve212_debug_analysis.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"   ✅ Visualisation debug sauvée: {output_file}")
    
    plt.close()

if __name__ == "__main__":
    coordinates = debug_leve212()
    
    print(f"\n✅ Debug terminé!")
    print(f"📁 Fichiers générés:")
    print(f"   - leve212_gray.png")
    print(f"   - leve212_denoised.png") 
    print(f"   - leve212_enhanced.png")
    print(f"   - leve212_binary.png")
    print(f"   - leve212_cleaned.png")
    print(f"   - leve212_debug_analysis.png")
