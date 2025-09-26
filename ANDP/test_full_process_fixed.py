#!/usr/bin/env python3
"""
Test script to run the full process and debug where the geometry error occurs
"""

import os
import sys
import tempfile

# Add Django project to path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_integration import OCRSpatialIntegrator
from ANDP_app.models import PublicUpload

def test_full_process():
    """Test the full process to see where it fails"""

    file_path = "Testing Data/leve3.jpg"

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    print("🔍 TESTING FULL PROCESS FOR leve3.jpg")
    print("=" * 60)

    try:
        # Create a PublicUpload instance
        with open(file_path, 'rb') as f:
            upload = PublicUpload.objects.create(
                file=f,
                original_filename="leve3.jpg"
            )

        print(f"✅ Created upload: {upload.id}")

        # Create integrator and process
        integrator = OCRSpatialIntegrator()

        print("📊 STARTING PROCESS...")
        result = integrator.process_upload_complete(upload)

        print("✅ PROCESS COMPLETED SUCCESSFULLY!")
        print(f"   Upload ID: {result['upload_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Coordinates extracted: {result['ocr_result']['coordinates_extracted']}")
        print(f"   Coordinates valid: {result['ocr_result']['coordinates_valid']}")
        print(f"   Parcel area: {result['parcel']['area']}")

    except Exception as e:
        print(f"❌ PROCESS FAILED: {str(e)}")
        print(f"   Error type: {type(e).__name__}")

        # Check upload status
        if 'upload' in locals():
            upload.refresh_from_db()
            print(f"   Upload status: {upload.processing_status}")
            print(f"   Error message: {upload.error_message}")
            print(f"   Processing log: {upload.processing_log}")

    finally:
        # Cleanup
        if 'upload' in locals():
            try:
                upload.delete()
            except:
                pass

if __name__ == "__main__":
    test_full_process()
