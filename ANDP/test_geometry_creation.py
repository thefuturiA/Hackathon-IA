#!/usr/bin/env python3
"""
Test création de géométrie pour les coordonnées de leve3.jpg
"""

import os
import sys

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from django.contrib.gis.geos import GEOSGeometry, Polygon

def test_geometry_creation():
    """Test création de géométrie avec les coordonnées extraites"""

    print("🔍 TEST CRÉATION GÉOMÉTRIE - leve3.jpg")
    print("="*50)

    # Coordonnées extraites de leve3.jpg
    coordinates = [
        {'borne': 'B1', 'x': 427094.70, 'y': 712773.67},
        {'borne': 'B2', 'x': 427110.61, 'y': 712767.66},
        {'borne': 'B3', 'x': 427103.58, 'y': 712748.94},
        {'borne': 'B4', 'x': 427099.06, 'y': 712746.69},
        {'borne': 'B5', 'x': 427084.21, 'y': 712750.65}
    ]

    print("📍 Coordonnées utilisées:")
    for coord in coordinates:
        print(f"   {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")

    try:
        # Créer le polygone
        coord_pairs = [(coord['x'], coord['y']) for coord in coordinates]

        # Vérifier si le polygone est fermé
        if coord_pairs[0] != coord_pairs[-1]:
            coord_pairs.append(coord_pairs[0])  # Fermer le polygone
            print("🔄 Polygone fermé automatiquement")

        print(f"📐 Création du polygone avec {len(coord_pairs)} points...")

        # Créer la géométrie
        polygon = Polygon(coord_pairs, srid=32631)

        # Calculer les métriques
        area = polygon.area  # m²
        perimeter = polygon.length  # m
        centroid = polygon.centroid

        print("✅ GÉOMÉTRIE CRÉÉE AVEC SUCCÈS!")
        print(f"   📏 Aire: {area:.2f} m²")
        print(f"   📐 Périmètre: {perimeter:.2f} m")
        print(f"   📍 Centroïde: X={centroid.x:.2f}, Y={centroid.y:.2f}")
        print(f"   🔺 Valide: {polygon.valid}")
        print(f"   🔄 Simple: {polygon.simple}")

        # Vérifier si le polygone est valide
        if not polygon.valid:
            print("⚠️  AVERTISSEMENT: Le polygone n'est pas valide selon GEOS")
            reasons = polygon.valid_reason
            print(f"   Raison: {reasons}")

        return True

    except Exception as e:
        print(f"❌ ERREUR lors de la création de géométrie: {str(e)}")
        print(f"   Type d'erreur: {type(e).__name__}")

        # Essayer de diagnostiquer le problème
        try:
            coord_pairs = [(coord['x'], coord['y']) for coord in coordinates]
            print(f"   📊 Points: {coord_pairs}")

            # Vérifier si les points sont colinéaires
            from shapely.geometry import Polygon as ShapelyPolygon
            shapely_poly = ShapelyPolygon(coord_pairs)
            print(f"   🔍 Shapely valide: {shapely_poly.is_valid}")
            if not shapely_poly.is_valid:
                print(f"   🔍 Raison Shapely: {shapely_poly.explain_validity()}")

        except Exception as diag_e:
            print(f"   🔍 Erreur diagnostic: {str(diag_e)}")

        return False

if __name__ == "__main__":
    success = test_geometry_creation()
    if success:
        print("\n🎉 La géométrie peut être créée - le problème est ailleurs!")
    else:
        print("\n💥 La géométrie ne peut pas être créée - c'est la source du problème!")
