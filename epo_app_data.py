import os
import json
import epo_ops
import xml.etree.ElementTree as ET
from datetime import datetime

# --- KONFIGURATION ---
FIRMEN = ['WFL'] 
DATA_FILE = 'app_patent_data.json'

def run_monitor():
    # 1. Zugangsdaten laden
    key = os.environ.get('EPO_KEY')
    secret = os.environ.get('EPO_SECRET')

    if not key or not secret:
        print("FEHLER: Keys nicht gefunden!")
        return

    client = epo_ops.Client(key=key, secret=secret)
    
    # 2. Bestehende Daten laden
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                all_patents = json.load(f)
            except:
                all_patents = []
    else:
        all_patents = []

    seen_ids = {p['id'] for p in all_patents}
    new_found = False

    for firma in FIRMEN:
        print(f"Suche nach: {firma}...")
        try:
            response = client.published_data_search(f'pa="{firma}"', 1, 100)
            root = ET.fromstring(response.content)
            
            # Alle Publikations-Referenzen finden
            publications = root.findall('.//{*}publication-reference')
            
            for pub in publications:
                doc_num = pub.find('.//{*}doc-number')
                country = pub.find('.//{*}country')
                
                if doc_num is not None and country is not None:
                    doc_id = country.text + doc_num.text
                    
                    if doc_id not in seen_ids:
                        # Echten Titel suchen
                        title_elem = pub.find('.//{*}title')
                        if title_elem is None:
                            # Suche im Dokument-Stamm nach dem Titel
                            title_elem = root.find(f".//{{*}}publication-reference[{{*}}doc-number='{doc_num.text}']..//{{*}}title")
                        
                        title = title_elem.text if title_elem is not None else "Titel nicht verfügbar"
                        date_elem = pub.find('.//{*}date')
                        date = date_elem.text if date_elem is not None else "---"
                        
                        all_patents.append({
                            "id": doc_id,
                            "firma": firma,
                            "titel": title,
                            "datum": date,
                            "url": f"https://worldwide.espacenet.com{doc_id[:2]}&NR={doc_id[2:]}",
                            "timestamp_added": datetime.now().isoformat()
                        })
                        seen_ids.add(doc_id)
                        new_found = True
        except Exception as e:
            print(f"Fehler bei {firma}: {e}")

    # 3. Speichern (Dieses Mal korrekt eingerückt!)
    all_patents.sort(key=lambda x: x.get('datum', '0000'), reverse=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_patents, f, indent=4, ensure_ascii=False)
    print("Update abgeschlossen.")

if __name__ == "__main__":
    run_monitor()
