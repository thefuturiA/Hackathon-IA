from services.topo import TopographyService
from ton_module import LayoutLMOracle  # ou PaddleOCROracle alias

if __name__ == "__main__":

    oracle = LayoutLMOracle(debug=False)
    coords = oracle.extract_coordinates("leve12.png")
    
    if not coords:
        print("Aucune coordonnée trouvée")
    else:
        for c in coords:
            print(f"{c['borne']}: X={c['x']}, Y={c['y']}")


from ton_module import LayoutLMOracle  # ou PaddleOCROracle alias

oracle = LayoutLMOracle(debug=False)
coords = oracle.extract_coordinates("leve12.png")

if not coords:
    print("Aucune coordonnée trouvée")
else:
    for c in coords:
        print(f"{c['borne']}: X={c['x']}, Y={c['y']}")
