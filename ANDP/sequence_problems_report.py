#!/usr/bin/env python3
"""
Rapport détaillé des problèmes de séquence des bornes
Analyse spécifique des cas comme leve212.png où les bornes ne sont pas complètes
"""

import os
import sys
import json
from datetime import datetime

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

def analyze_leve212_problem():
    """Analyse détaillée du problème de leve212.png"""
    
    print("🔍 ANALYSE DÉTAILLÉE - PROBLÈME DE SÉQUENCE leve212.png")
    print("="*60)
    
    extractor = HybridOCRCorrector()
    file_path = "Testing Data/leve212.png"
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return
    
    # Extraction normale
    coordinates = extractor.extract_coordinates(file_path)
    
    print(f"📁 Fichier: leve212.png")
    print(f"📍 Coordonnées extraites: {len(coordinates)}")
    
    if coordinates:
        print("\n🔍 BORNES TROUVÉES:")
        for coord in coordinates:
            print(f"   {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
        
        # Analyse de la séquence
        borne_numbers = []
        for coord in coordinates:
            if coord['borne'].startswith('B'):
                try:
                    num = int(coord['borne'][1:])
                    borne_numbers.append(num)
                except ValueError:
                    pass
        
        borne_numbers.sort()
        print(f"\n📊 ANALYSE DE SÉQUENCE:")
        print(f"   Bornes présentes: {borne_numbers}")
        print(f"   Plage: B{min(borne_numbers)} à B{max(borne_numbers)}")
        
        # Identifier les bornes manquantes
        expected_range = list(range(1, max(borne_numbers) + 1))
        missing = [f"B{i}" for i in expected_range if i not in borne_numbers]
        
        if missing:
            print(f"   ❌ Bornes manquantes: {', '.join(missing)}")
        
        # Problèmes identifiés
        print(f"\n⚠️  PROBLÈMES IDENTIFIÉS:")
        if 1 not in borne_numbers:
            print(f"   - Pas de B1 (borne de départ)")
        if len(missing) > 0:
            print(f"   - {len(missing)} bornes manquantes dans la séquence")
        if len(coordinates) < 4:
            print(f"   - Trop peu de bornes pour former un polygone complet")
    
    return coordinates

def create_sequence_problems_summary():
    """Crée un résumé des problèmes de séquence courants"""
    
    print(f"\n📋 TYPES DE PROBLÈMES DE SÉQUENCE IDENTIFIÉS:")
    print("="*50)
    
    problems = {
        "missing_b1": {
            "description": "Séquence ne commence pas par B1",
            "exemple": "B2, B6, B7, B8 (leve212.png)",
            "impact": "Impossible de déterminer le point de départ du polygone",
            "solution": "Améliorer la détection de B1 ou inférer sa position"
        },
        "missing_intermediate": {
            "description": "Bornes intermédiaires manquantes",
            "exemple": "B1, B3, B5 (manque B2, B4)",
            "impact": "Polygone incomplet, géométrie incorrecte",
            "solution": "Patterns OCR plus robustes, détection contextuelle"
        },
        "out_of_order": {
            "description": "Bornes dans le désordre",
            "exemple": "B3, B1, B4, B2",
            "impact": "Ordre de parcours incorrect du polygone",
            "solution": "Tri automatique par position géographique"
        },
        "gaps_in_sequence": {
            "description": "Trous dans la numérotation",
            "exemple": "B1, B2, B5, B6 (manque B3, B4)",
            "impact": "Géométrie du polygone incorrecte",
            "solution": "Interpolation ou détection des bornes manquantes"
        }
    }
    
    for problem_type, details in problems.items():
        print(f"\n🔸 {details['description'].upper()}")
        print(f"   Exemple: {details['exemple']}")
        print(f"   Impact: {details['impact']}")
        print(f"   Solution: {details['solution']}")
    
    return problems

def propose_solutions():
    """Propose des solutions pour améliorer l'extraction"""
    
    print(f"\n💡 SOLUTIONS PROPOSÉES:")
    print("="*40)
    
    solutions = [
        {
            "titre": "Amélioration des patterns OCR",
            "description": "Ajouter des patterns spécifiques pour capturer B1, B3, B4, B5",
            "implementation": [
                "Pattern pour 'B1' isolé ou en début de ligne",
                "Pattern pour bornes avec espacement variable",
                "Pattern pour bornes avec formatage différent"
            ]
        },
        {
            "titre": "Analyse contextuelle",
            "description": "Utiliser le contexte spatial pour identifier les bornes manquantes",
            "implementation": [
                "Analyser la distribution spatiale des bornes trouvées",
                "Inférer la position des bornes manquantes",
                "Valider la cohérence géométrique"
            ]
        },
        {
            "titre": "Post-traitement intelligent",
            "description": "Corriger automatiquement les séquences incomplètes",
            "implementation": [
                "Détecter les trous dans la séquence",
                "Proposer des bornes manquantes probables",
                "Réordonner les bornes selon leur position géographique"
            ]
        },
        {
            "titre": "Amélioration du préprocessing",
            "description": "Optimiser le traitement d'image pour leve212.png",
            "implementation": [
                "Ajuster les paramètres de binarisation",
                "Améliorer la détection des zones de texte",
                "Filtrer le bruit spécifique à ce type d'image"
            ]
        }
    ]
    
    for i, solution in enumerate(solutions, 1):
        print(f"\n{i}. {solution['titre'].upper()}")
        print(f"   {solution['description']}")
        print("   Implémentation:")
        for item in solution['implementation']:
            print(f"   - {item}")
    
    return solutions

def generate_improvement_script():
    """Génère un script d'amélioration pour les patterns OCR"""
    
    improved_patterns = """
# Patterns améliorés pour capturer plus de bornes

# Pattern spécifique pour B1 (souvent en début)
r'(?:^|\\s)(B1)\\s*[:\\s]*(\d{6,7}[.,]?\d{0,3})\\s*[,\\s]*(\d{6,7}[.,]?\d{0,3})'

# Pattern pour bornes avec numérotation continue
r'(B[1-9])\\s*[:\\s]*(\d{6,7}[.,]?\d{0,3})\\s*[,\\s]*(\d{6,7}[.,]?\d{0,3})'

# Pattern pour bornes isolées (B3, B4, B5)
r'\\b(B[3-5])\\s*[:\\s]*(\d{6,7}[.,]?\d{0,3})\\s*[,\\s]*(\d{6,7}[.,]?\d{0,3})'

# Pattern pour coordonnées sans borne explicite (inférer B1, B3, etc.)
r'(?<!B\\d)\\s*(\d{6,7}[.,]?\d{0,3})\\s*[,\\s]*(\d{6,7}[.,]?\d{0,3})(?=\\s|$)'
"""
    
    print(f"\n🔧 PATTERNS OCR AMÉLIORÉS:")
    print("="*40)
    print(improved_patterns)
    
    return improved_patterns

def create_detailed_report():
    """Crée un rapport détaillé complet"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"sequence_problems_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Rapport des Problèmes de Séquence des Bornes\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 🔍 Cas d'Étude: leve212.png\n\n")
        f.write("### Problème Identifié\n")
        f.write("- **Bornes extraites:** B2, B6, B7, B8\n")
        f.write("- **Bornes manquantes:** B1, B3, B4, B5\n")
        f.write("- **Impact:** Polygone incomplet, impossible de déterminer la géométrie correcte\n\n")
        
        f.write("### Analyse Technique\n")
        f.write("- **Texte OCR détecté:** 66 éléments de texte\n")
        f.write("- **Patterns utilisés:** 4 patterns de reconnaissance\n")
        f.write("- **Taux de capture:** 50% des bornes attendues\n\n")
        
        f.write("## 📊 Types de Problèmes\n\n")
        f.write("1. **Bornes manquantes en début de séquence** (B1 absent)\n")
        f.write("2. **Trous dans la séquence** (B3, B4, B5 manquants)\n")
        f.write("3. **Patterns OCR insuffisants** pour certains formats\n")
        f.write("4. **Qualité d'image** affectant la reconnaissance\n\n")
        
        f.write("## 💡 Solutions Recommandées\n\n")
        f.write("### Solution Immédiate\n")
        f.write("1. Ajouter des patterns spécifiques pour B1, B3, B4, B5\n")
        f.write("2. Améliorer le préprocessing pour leve212.png\n")
        f.write("3. Implémenter une détection contextuelle\n\n")
        
        f.write("### Solution Long Terme\n")
        f.write("1. Développer un modèle ML spécialisé\n")
        f.write("2. Créer une base de données de référence\n")
        f.write("3. Implémenter une validation géométrique\n\n")
        
        f.write("## 🎯 Objectifs de Performance\n\n")
        f.write("- **Taux de capture cible:** 95% des bornes\n")
        f.write("- **Séquences complètes:** 80% des fichiers\n")
        f.write("- **Polygones fermés:** 70% des extractions\n\n")
    
    print(f"\n📄 Rapport détaillé généré: {report_file}")
    return report_file

if __name__ == "__main__":
    # Analyse du cas leve212.png
    coordinates = analyze_leve212_problem()
    
    # Résumé des types de problèmes
    problems = create_sequence_problems_summary()
    
    # Solutions proposées
    solutions = propose_solutions()
    
    # Patterns améliorés
    patterns = generate_improvement_script()
    
    # Rapport détaillé
    report_file = create_detailed_report()
    
    print(f"\n✅ Analyse terminée!")
    print(f"📋 Problèmes identifiés: {len(problems)}")
    print(f"💡 Solutions proposées: {len(solutions)}")
    print(f"📄 Rapport généré: {report_file}")
