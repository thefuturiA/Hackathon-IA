import os
import json
from typing import List, Dict, Tuple
from .ocr_extraction import HybridOCRCorrector
from .topo import TopographyService
import cv2
import numpy as np

class TopoTrainingService:
    """
    Service pour entraîner et tester l'extraction de coordonnées 
    sur les levées topographiques du Bénin
    """
    
    def __init__(self, training_data_path: str = "Testing Data"):
        self.training_data_path = training_data_path
        self.ocr_extractor = HybridOCRCorrector()
        self.topo_service = TopographyService(debug=True)
        self.results = []
        
    def get_training_files(self) -> List[str]:
        """Récupère tous les fichiers d'entraînement"""
        if not os.path.exists(self.training_data_path):
            print(f"Dossier {self.training_data_path} non trouvé")
            return []
            
        files = []
        for filename in os.listdir(self.training_data_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(os.path.join(self.training_data_path, filename))
        
        return sorted(files)
    
    def extract_from_single_file(self, file_path: str) -> Dict:
        """Extrait les coordonnées d'un seul fichier"""
        print(f"\n=== Traitement de {os.path.basename(file_path)} ===")
        
        try:
            # Extraction avec OCR hybride
            coordinates = self.ocr_extractor.extract_coordinates(file_path)
            
            result = {
                'file': os.path.basename(file_path),
                'path': file_path,
                'coordinates': coordinates,
                'count': len(coordinates),
                'status': 'success' if coordinates else 'no_coords_found'
            }
            
            # Affichage des résultats
            if coordinates:
                print(f"✅ {len(coordinates)} coordonnées trouvées:")
                for coord in coordinates:
                    print(f"   {coord['borne']}: X={coord['x']}, Y={coord['y']}")
                    
                # Vérification de fermeture du polygone
                if len(coordinates) >= 3:
                    is_closed = self.ocr_extractor.is_polygon_closed(coordinates)
                    result['polygon_closed'] = is_closed
                    print(f"   Polygone fermé: {'✅' if is_closed else '❌'}")
            else:
                print("❌ Aucune coordonnée trouvée")
                
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            result = {
                'file': os.path.basename(file_path),
                'path': file_path,
                'coordinates': [],
                'count': 0,
                'status': 'error',
                'error': str(e)
            }
            
        return result
    
    def batch_extract(self, limit: int = None) -> List[Dict]:
        """Traite tous les fichiers d'entraînement"""
        files = self.get_training_files()
        
        if limit:
            files = files[:limit]
            
        print(f"🚀 Début du traitement de {len(files)} fichiers...")
        
        results = []
        for i, file_path in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}]", end=" ")
            result = self.extract_from_single_file(file_path)
            results.append(result)
            
        self.results = results
        return results
    
    def analyze_results(self) -> Dict:
        """Analyse les résultats d'extraction"""
        if not self.results:
            return {}
            
        total_files = len(self.results)
        successful_extractions = len([r for r in self.results if r['count'] > 0])
        total_coordinates = sum(r['count'] for r in self.results)
        
        # Statistiques par nombre de bornes
        coord_counts = {}
        for result in self.results:
            count = result['count']
            coord_counts[count] = coord_counts.get(count, 0) + 1
        
        # Fichiers problématiques
        no_coords = [r['file'] for r in self.results if r['count'] == 0]
        errors = [r for r in self.results if r['status'] == 'error']
        
        analysis = {
            'total_files': total_files,
            'successful_extractions': successful_extractions,
            'success_rate': (successful_extractions / total_files) * 100,
            'total_coordinates': total_coordinates,
            'avg_coordinates_per_file': total_coordinates / total_files if total_files > 0 else 0,
            'coordinate_distribution': coord_counts,
            'files_without_coords': no_coords,
            'errors': errors
        }
        
        return analysis
    
    def print_analysis(self):
        """Affiche l'analyse des résultats"""
        analysis = self.analyze_results()
        
        print("\n" + "="*60)
        print("📊 ANALYSE DES RÉSULTATS")
        print("="*60)
        
        print(f"📁 Fichiers traités: {analysis['total_files']}")
        print(f"✅ Extractions réussies: {analysis['successful_extractions']}")
        print(f"📈 Taux de réussite: {analysis['success_rate']:.1f}%")
        print(f"📍 Total coordonnées: {analysis['total_coordinates']}")
        print(f"📊 Moyenne par fichier: {analysis['avg_coordinates_per_file']:.1f}")
        
        print(f"\n📋 Distribution des coordonnées:")
        for count, files in sorted(analysis['coordinate_distribution'].items()):
            print(f"   {count} coordonnées: {files} fichiers")
        
        if analysis['files_without_coords']:
            print(f"\n❌ Fichiers sans coordonnées ({len(analysis['files_without_coords'])}):")
            for filename in analysis['files_without_coords'][:10]:  # Limite à 10
                print(f"   - {filename}")
            if len(analysis['files_without_coords']) > 10:
                print(f"   ... et {len(analysis['files_without_coords']) - 10} autres")
        
        if analysis['errors']:
            print(f"\n🚨 Erreurs ({len(analysis['errors'])}):")
            for error in analysis['errors'][:5]:  # Limite à 5
                print(f"   - {error['file']}: {error['error']}")
    
    def save_results(self, output_file: str = "training_results.json"):
        """Sauvegarde les résultats en JSON"""
        if not self.results:
            print("Aucun résultat à sauvegarder")
            return
            
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'results': self.results,
                'analysis': self.analyze_results()
            }, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Résultats sauvegardés dans {output_file}")
    
    def test_specific_files(self, filenames: List[str]):
        """Teste des fichiers spécifiques"""
        print(f"🎯 Test de fichiers spécifiques: {filenames}")
        
        for filename in filenames:
            file_path = os.path.join(self.training_data_path, filename)
            if os.path.exists(file_path):
                self.extract_from_single_file(file_path)
            else:
                print(f"❌ Fichier non trouvé: {filename}")


def main():
    """Fonction principale pour tester l'extraction"""
    trainer = TopoTrainingService()
    
    # Test sur quelques fichiers d'abord
    print("🧪 Test sur 5 premiers fichiers...")
    results = trainer.batch_extract(limit=5)
    trainer.print_analysis()
    
    # Demander si continuer avec tous les fichiers
    response = input("\n❓ Continuer avec tous les fichiers? (y/N): ")
    if response.lower() == 'y':
        print("\n🚀 Traitement de tous les fichiers...")
        results = trainer.batch_extract()
        trainer.print_analysis()
        trainer.save_results()


if __name__ == "__main__":
    main()
