#!/usr/bin/env python3
"""
Test visuel pour analyser l'extraction de coordonnées sur leve1.jpg
"""

import os
import sys
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

def test_leve1_visual():
    """Test visuel détaillé sur leve1.jpg"""
    
    print("🔍 ANALYSE VISUELLE - leve1.jpg")
    print("="*50)
    
    # Chemin du fichier
    file_path = "Testing Data/leve2.jpg"
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return
    
    # Initialiser l'extracteur
    extractor = HybridOCRCorrector()
    
    print(f"📁 Fichier: {file_path}")
    print(f"📏 Analyse de l'image...")
    
    # Charger l'image originale
    original_img = cv2.imread(file_path)
    if original_img is None:
        print("❌ Impossible de charger l'image")
        return
    
    height, width = original_img.shape[:2]
    print(f"   Dimensions: {width}x{height} pixels")
    
    # Extraction des coordonnées avec détails
    print(f"\n🔍 Extraction des coordonnées...")
    coordinates = extractor.extract_coordinates(file_path)
    
    print(f"\n📊 RÉSULTATS D'EXTRACTION:")
    print(f"   Coordonnées trouvées: {len(coordinates)}")
    
    if coordinates:
        print(f"\n📍 DÉTAIL DES COORDONNÉES:")
        for i, coord in enumerate(coordinates, 1):
            is_valid = extractor.validate_coordinates(coord['x'], coord['y'])
            status = "✅ Valide" if is_valid else "❌ Invalide"
            print(f"   {i}. {coord['borne']}: X={coord['x']:>10.2f}, Y={coord['y']:>10.2f} - {status}")
        
        # Analyse géométrique
        print(f"\n📐 ANALYSE GÉOMÉTRIQUE:")
        x_coords = [c['x'] for c in coordinates]
        y_coords = [c['y'] for c in coordinates]
        
        print(f"   Plage X: {min(x_coords):.2f} - {max(x_coords):.2f} (Δ={max(x_coords)-min(x_coords):.2f}m)")
        print(f"   Plage Y: {min(y_coords):.2f} - {max(y_coords):.2f} (Δ={max(y_coords)-min(y_coords):.2f}m)")
        
        # Centre du polygone
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        print(f"   Centre: X={center_x:.2f}, Y={center_y:.2f}")
        
        # Test de fermeture
        if len(coordinates) >= 3:
            is_closed = extractor.is_polygon_closed(coordinates)
            print(f"   Polygone fermé: {'✅ Oui' if is_closed else '❌ Non'}")
            
            if not is_closed and len(coordinates) >= 3:
                first, last = coordinates[0], coordinates[-1]
                distance = ((first['x'] - last['x'])**2 + (first['y'] - last['y'])**2)**0.5
                print(f"   Distance première-dernière borne: {distance:.2f}m")
        
        # Calcul de la superficie approximative (si polygone)
        if len(coordinates) >= 3:
            # Formule du lacet pour calculer l'aire
            area = 0
            n = len(coordinates)
            for i in range(n):
                j = (i + 1) % n
                area += coordinates[i]['x'] * coordinates[j]['y']
                area -= coordinates[j]['x'] * coordinates[i]['y']
            area = abs(area) / 2
            
            # Conversion en hectares, ares, centiares
            hectares = int(area // 10000)
            ares = int((area % 10000) // 100)
            centiares = int(area % 100)
            
            print(f"   Superficie calculée: {area:.2f} m² ({hectares:02d}ha {ares:02d}a {centiares:02d}ca)")
    
    else:
        print("   ❌ Aucune coordonnée extraite")
    
    # Analyse de l'image préprocessée
    print(f"\n🖼️  ANALYSE DE L'IMAGE PRÉPROCESSÉE:")
    preprocessed_img = extractor.preprocess_image(file_path)
    print(f"   Image préprocessée: {preprocessed_img.shape}")
    
    # Sauvegarde de l'image préprocessée pour inspection
    cv2.imwrite("leve1_preprocessed.png", preprocessed_img)
    print(f"   ✅ Image préprocessée sauvée: leve1_preprocessed.png")
    
    # Création d'une visualisation
    create_coordinate_visualization(file_path, coordinates)
    
    return coordinates

def create_coordinate_visualization(image_path, coordinates):
    """Crée une visualisation des coordonnées extraites"""
    
    if not coordinates:
        print("   ⚠️  Pas de coordonnées à visualiser")
        return
    
    print(f"\n📈 CRÉATION DE LA VISUALISATION...")
    
    # Charger l'image originale
    img = Image.open(image_path)
    
    # Créer la figure avec deux sous-graphiques
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Graphique 1: Image originale
    ax1.imshow(img)
    ax1.set_title("Image Originale - leve1.jpg", fontsize=14, fontweight='bold')
    ax1.axis('off')
    
    # Graphique 2: Plan des coordonnées
    x_coords = [c['x'] for c in coordinates]
    y_coords = [c['y'] for c in coordinates]
    
    # Tracer les points
    ax2.scatter(x_coords, y_coords, c='red', s=100, zorder=5)
    
    # Tracer les lignes du polygone
    if len(coordinates) >= 3:
        # Fermer le polygone
        x_poly = x_coords + [x_coords[0]]
        y_poly = y_coords + [y_coords[0]]
        ax2.plot(x_poly, y_poly, 'b-', linewidth=2, alpha=0.7)
        ax2.fill(x_poly, y_poly, alpha=0.2, color='blue')
    
    # Annoter les points
    for i, coord in enumerate(coordinates):
        ax2.annotate(coord['borne'], 
                    (coord['x'], coord['y']), 
                    xytext=(5, 5), 
                    textcoords='offset points',
                    fontsize=10, 
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    # Configuration du graphique des coordonnées
    ax2.set_xlabel('X (UTM)', fontsize=12)
    ax2.set_ylabel('Y (UTM)', fontsize=12)
    ax2.set_title('Coordonnées Extraites (UTM)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')
    
    # Ajuster les marges
    margin_x = (max(x_coords) - min(x_coords)) * 0.1
    margin_y = (max(y_coords) - min(y_coords)) * 0.1
    ax2.set_xlim(min(x_coords) - margin_x, max(x_coords) + margin_x)
    ax2.set_ylim(min(y_coords) - margin_y, max(y_coords) + margin_y)
    
    # Ajouter les informations
    info_text = f"Bornes: {len(coordinates)}\n"
    info_text += f"X: {min(x_coords):.1f} - {max(x_coords):.1f}\n"
    info_text += f"Y: {min(y_coords):.1f} - {max(y_coords):.1f}"
    
    ax2.text(0.02, 0.98, info_text, 
            transform=ax2.transAxes, 
            verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8),
            fontsize=10)
    
    plt.tight_layout()
    
    # Sauvegarder la visualisation
    output_file = "leve1_coordinate_analysis.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"   ✅ Visualisation sauvée: {output_file}")
    
    plt.close()

def display_coordinate_table(coordinates):
    """Affiche un tableau formaté des coordonnées"""
    
    if not coordinates:
        return
    
    print(f"\n📋 TABLEAU DES COORDONNÉES:")
    print("   " + "="*60)
    print("   | Borne |      X (UTM)      |      Y (UTM)      | Valide |")
    print("   " + "="*60)
    
    extractor = HybridOCRCorrector()
    for coord in coordinates:
        is_valid = extractor.validate_coordinates(coord['x'], coord['y'])
        status = "✅" if is_valid else "❌"
        print(f"   | {coord['borne']:>5} | {coord['x']:>15.2f} | {coord['y']:>15.2f} |   {status}   |")
    
    print("   " + "="*60)

if __name__ == "__main__":
    coordinates = test_leve1_visual()
    if coordinates:
        display_coordinate_table(coordinates)
    
    print(f"\n✅ Analyse terminée!")
    print(f"📁 Fichiers générés:")
    print(f"   - leve1_preprocessed.png (image préprocessée)")
    print(f"   - leve1_coordinate_analysis.png (visualisation)")
