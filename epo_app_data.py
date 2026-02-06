import os
import json
import epo_ops
import xml.etree.ElementTree as ET
from datetime import datetime

# --- KONFIGURATION ---
# Hier deine Firmen eintragen
FIRMEN = ['WFL Millturn', 'Siemens AG'] 
DATA_FILE = 'app_patent_data.json'

def run_monitor():
    # 1. Secrets aus Umgebungsvariablen laden
    key = os.environ.get('EPO_KEY')
    secret = os.environ.get('EPO_SECRET')

    if not key or not secret:
        print("FEHLER: EPO_KEY oder EPO_SECRET nicht gefunden!")
        return

    # 2. EPO Client initialisieren
    client = epo_ops.Client(key=key, secret=secret)
    
    # 3. Bestehende Daten laden
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                all_patents = json.load(f)
            except json.JSONDecodeError:
                all_patents = []
    else:
        all_patents = []

    seen_ids = {p['id'] for p in all_patents}
    new_found = False

    # Namespace-Definition des EPA
    ns = {'exchange': 'http://www.epo.org'}

    for firma in FIRMEN:
        print(f"Suche nach: {firma}...")
        try:
            # Der Aufruf erfolgt ohne Keyword-Argumente für maximale Kompatibilität
            response = client.published_data_search(f'pa="{firma}"', 1, 50)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            for item in root.findall('.//exchange:item', ns):
                doc_id = item.get('epodoc-id')
                
                if doc_id not in seen_ids:
                    title_elem = item.find('.//exchange:title', ns)
                    title = title_elem.text if title_elem is not None else "Kein Titel"
                    
                    date_elem = item.find('.//exchange:publication-reference//exchange:date', ns)
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
            print(f"Fehler bei Firma {firma}: {e}")

    # 4. Speichern, falls neue Daten gefunden wurden
    if new_found:
        all_patents.sort(key=lambda x: x['datum'], reverse=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_patents, f, indent=4, ensure_ascii=False)
        print(f"Update erfolgreich: {len(all_patents)} Patente insgesamt.")
    else:
        print("Keine neuen Patente gefunden.")

if __name__ == "__main__":
    run_monitor()
