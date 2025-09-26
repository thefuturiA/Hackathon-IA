#!/usr/bin/env python3
"""
Test script to extract coordinates from leve3.jpg and debug the geometry issue
"""

import os
import sys

# Add Django project to path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction_ultra_precise import UltraPreciseCoordinateExtractor

def test_leve3_extraction():
    """Extract coordinates from leve3.jpg and show details"""

    file_path = "Testing Data/leve3.jpg"

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    print("🔍 TESTING COORDINATE EXTRACTION FROM leve3.jpg")
    print("=" * 60)

    extractor = UltraPreciseCoordinateExtractor()

    try:
        # Extract coordinates
        print("📊 EXTRACTING COORDINATES...")
        coordinates = extractor.extract_coordinates(file_path)

        print(f"✅ Found {len(coordinates)} coordinates:")
        print("-" * 40)

        if coordinates:
            for i, coord in enumerate(coordinates, 1):
                print(f"{i}. {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")

            # Check if we have enough for a polygon
            if len(coordinates) < 3:
                print(f"\n❌ INSUFFICIENT COORDINATES: Need at least 3, got {len(coordinates)}")
                return coordinates

            # Try to create geometry
            print("\n🏗️  TESTING GEOMETRY CREATION...")
            try:
                from ANDP_app.services.ocr_integration import coords_to_polygon_wkt
                wkt = coords_to_polygon_wkt(coordinates)
                print(f"✅ Valid WKT created: {wkt[:100]}...")

                # Try to create GEOS geometry
                from django.contrib.gis.geos import GEOSGeometry
                geom = GEOSGeometry(wkt, srid=32631)
                print(f"✅ Valid geometry created: {geom.geom_type} with area {geom.area:.2f}")

            except Exception as e:
                print(f"❌ GEOMETRY CREATION FAILED: {str(e)}")
                print("   This is why the API returns 'Géométrie invalide'")

        else:
            print("❌ NO COORDINATES EXTRACTED")
            print("   This is why geometry creation fails")

    except Exception as e:
        print(f"❌ EXTRACTION ERROR: {str(e)}")

    return coordinates

if __name__ == "__main__":
    coords = test_leve3_extraction()
