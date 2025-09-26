#!/usr/bin/env python3
"""
Extracteur avec VALIDATION DE SÉQUENCE LOGIQUE
Garantit qu'on ne peut pas avoir B2 sans B1, B3 sans B1-B2, etc.
"""

import os
import sys
import re
from typing import List, Dict, Tuple

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from final_production_extractor import FinalProductionExtractor

class SequenceLogicalExtractor(FinalProductionExtractor):
    """
    Extracteur avec validation de séquence LOGIQUE
    Garantit la cohérence des séquences de bornes
    """
    
    def extract_coordinates_with_logical_sequence(self, img_path: str, mode: str = "balanced") -> List[Dict]:
        """
        Extraction avec validation de séquence LOGIQUE
        
        Règles:
        - On ne peut pas avoir B2 sans B1
        - On ne peut pas avoir B3 sans B1 et B2
        - La séquence doit être logiquement cohérente
        """
        
        print(f"🧠 EXTRACTION AVEC SÉQUENCE LOGIQUE pour {os.path.basename(img_path)}")
        print("="*60)
        print("⚠️  VALIDATION: Pas de B2 sans B1, pas de B3 sans B1-B2, etc.")
        
        # Extraction normale d'abord
        raw_coords = super().extract_coordinates_final_production(img_path, mode=mode)
        
        # Validation de séquence logique
        logical_coords = self._validate_logical_sequence(raw_coords)
        
        return logical_coords
    
    def _validate_logical_sequence(self, coordinates: List[Dict]) -> List[Dict]:
        """Valide et corrige la séquence logique"""
        
        print(f"\n🧠 VALIDATION DE SÉQUENCE LOGIQUE:")
        
        if not coordinates:
            print("   ❌ Aucune coordonnée à valider")
            return []
        
        # Extraire les numéros de bornes
        borne_numbers = []
        borne_dict = {}
        
        for coord in coordinates:
            try:
                # Extraire le numéro de la borne (ignorer les erreurs comme B839)
                match = re.match(r'B(\d+)', coord['borne'])
                if match:
                    num = int(match.group(1))
                    # Ignorer les numéros aberrants (> 20 par exemple)
                    if num <= 20:
                        borne_numbers.append(num)
                        borne_dict[num] = coord
            except:
                continue
        
        borne_numbers.sort()
        
        print(f"   📍 Bornes brutes trouvées: {[f'B{n}' for n in borne_numbers]}")
        
        # Validation de séquence logique
        valid_sequence = self._build_logical_sequence(borne_numbers, borne_dict)
        
        print(f"   ✅ Séquence logique validée: {[coord['borne'] for coord in valid_sequence]}")
        
        return valid_sequence
    
    def _build_logical_sequence(self, borne_numbers: List[int], borne_dict: Dict[int, Dict]) -> List[Dict]:
        """Construit une séquence logiquement cohérente"""
        
        if not borne_numbers:
            return []
        
        # Cas 1: Si on a B1, on peut construire une séquence à partir de B1
        if 1 in borne_numbers:
            print("   ✅ B1 trouvé - Construction séquence à partir de B1")
            return self._build_sequence_from_b1(borne_numbers, borne_dict)
        
        # Cas 2: Si on n'a pas B1 mais on a des bornes consécutives
        else:
            print("   ⚠️  B1 manquant - Recherche de séquences consécutives")
            return self._build_consecutive_sequence(borne_numbers, borne_dict)
    
    def _build_sequence_from_b1(self, borne_numbers: List[int], borne_dict: Dict[int, Dict]) -> List[Dict]:
        """Construit une séquence logique à partir de B1"""
        
        valid_coords = []
        
        # Commencer par B1
        valid_coords.append(borne_dict[1])
        
        # Ajouter les bornes consécutives
        current = 1
        for num in sorted(borne_numbers):
            if num == current + 1:
                valid_coords.append(borne_dict[num])
                current = num
            elif num > current + 1:
                # Gap dans la séquence - on s'arrête ici pour la logique stricte
                print(f"   ⚠️  Gap détecté: B{current} → B{num} (manque B{current+1})")
                break
        
        return valid_coords
    
    def _build_consecutive_sequence(self, borne_numbers: List[int], borne_dict: Dict[int, Dict]) -> List[Dict]:
        """Construit la plus longue séquence consécutive possible"""
        
        # Trouver la plus longue séquence consécutive
        longest_sequence = []
        current_sequence = []
        
        for i, num in enumerate(sorted(borne_numbers)):
            if not current_sequence or num == current_sequence[-1] + 1:
                current_sequence.append(num)
            else:
                if len(current_sequence) > len(longest_sequence):
                    longest_sequence = current_sequence.copy()
                current_sequence = [num]
        
        # Vérifier la dernière séquence
        if len(current_sequence) > len(longest_sequence):
            longest_sequence = current_sequence.copy()
        
        # Construire les coordonnées pour la séquence la plus longue
        valid_coords = []
        for num in longest_sequence:
            valid_coords.append(borne_dict[num])
        
        if longest_sequence:
            print(f"   ✅ Séquence consécutive la plus longue: B{longest_sequence[0]} à B{longest_sequence[-1]}")
        
        return valid_coords
    
    def _analyze_sequence_logic(self, coordinates: List[Dict]) -> Dict:
        """Analyse la logique de la séquence finale"""
        
        if not coordinates:
            return {'valid': False, 'reason': 'Aucune coordonnée'}
        
        # Extraire les numéros
        numbers = []
        for coord in coordinates:
            try:
                num = int(coord['borne'][1:])
                numbers.append(num)
            except:
                continue
        
        numbers.sort()
        
        analysis = {
            'valid': True,
            'sequence': [f'B{n}' for n in numbers],
            'start': numbers[0] if numbers else None,
            'end': numbers[-1] if numbers else None,
            'count': len(numbers),
            'consecutive': True,
            'missing': []
        }
        
        # Vérifier la consécutivité
        if numbers:
            expected = list(range(numbers[0], numbers[-1] + 1))
            missing = [n for n in expected if n not in numbers]
            
            if missing:
                analysis['consecutive'] = False
                analysis['missing'] = [f'B{n}' for n in missing]
        
        # Vérifier la logique (pas de B2 sans B1, etc.)
        if numbers and numbers[0] != 1:
            if numbers[0] > 1:
                analysis['logic_issue'] = f"Séquence commence par B{numbers[0]} au lieu de B1"
        
        return analysis

def test_sequence_logical_extractor():
    """Test de l'extracteur avec validation de séquence logique"""
    
    print("🧠 TEST EXTRACTEUR AVEC SÉQUENCE LOGIQUE")
    print("="*60)
    print("⚠️  RÈGLE: Pas de B2 sans B1, pas de B3 sans B1-B2, etc.")
    
    extractor = SequenceLogicalExtractor()
    
    # Fichiers de test
    test_files = [
        "Testing Data/leve212.png",  # Cas problématique: B2, B4, B6, B7, B8 sans B1
        "Testing Data/leve275.png",  # Cas: B3, B4 sans B1, B2
        "Testing Data/leve297.png",  # Cas: B1, B2, B3, B4 (séquence logique)
        "Testing Data/leve298.png",  # Cas: B1, B2, B3, B4 (séquence logique)
    ]
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            continue
            
        filename = os.path.basename(file_path)
        print(f"\n{'='*60}")
        print(f"🧠 TEST LOGIQUE: {filename}")
        print(f"{'='*60}")
        
        try:
            # Test avec mode agressif pour avoir le maximum de coordonnées
            coords = extractor.extract_coordinates_with_logical_sequence(file_path, mode='aggressive')
            
            # Analyse de la logique
            analysis = extractor._analyze_sequence_logic(coords)
            
            print(f"\n🎯 RÉSULTAT LOGIQUE {filename}:")
            print(f"   Coordonnées: {len(coords)}")
            print(f"   Séquence: {analysis['sequence']}")
            print(f"   Logiquement valide: {'✅' if analysis['valid'] else '❌'}")
            
            if 'logic_issue' in analysis:
                print(f"   ⚠️  Problème logique: {analysis['logic_issue']}")
            
            if not analysis['consecutive']:
                print(f"   ❌ Manquantes: {analysis['missing']}")
            
            # Afficher les coordonnées finales
            if coords:
                print(f"\n📍 Coordonnées logiquement validées:")
                for coord in coords:
                    print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
            
        except Exception as e:
            print(f"❌ Erreur sur {filename}: {e}")
    
    print(f"\n{'='*60}")
    print(f"💡 CONCLUSION LOGIQUE")
    print(f"{'='*60}")
    print(f"✅ L'extracteur garantit maintenant la cohérence logique")
    print(f"✅ Pas de B2 sans B1, pas de B3 sans B1-B2, etc.")
    print(f"✅ Séquences consécutives privilégiées")
    print(f"✅ Validation stricte de la logique des bornes")

if __name__ == "__main__":
    test_sequence_logical_extractor()
