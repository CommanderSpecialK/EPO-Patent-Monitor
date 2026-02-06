import os
import json
import epo_ops
import xml.etree.ElementTree as ET
from datetime import datetime

# --- KONFIGURATION ---
# Hier deine Firmen eintragen
FIRMEN = ['WFL'] 
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
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
        # ensure_ascii=False ist wichtig für Umlaute etc.
        json.dump(all_patents, f, indent=4, ensure_ascii=False)
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
            response = client.published_data_search(f'pa="{firma}"', 1, 100)
            response.raise_for_status()
            
            # Wir parsen den gesamten Text
            xml_content = response.text
            root = ET.fromstring(xml_content)
            
            # Das EPA nutzt in der Suche 'publication-reference' statt 'item'
            # Wir suchen nach JEDER Referenz im Dokument
            publications = root.findall('.//{*}publication-reference')
            print(f"DEBUG: {len(publications)} Publikationen im XML gefunden")

            for pub in publications:
                # 1. ID extrahieren (aus dem document-id Feld)
                # Wir suchen die doc-number und das country
                doc_num_elem = pub.find('.//{*}doc-number')
                country_elem = pub.find('.//{*}country')
                
                if doc_num_elem is not None and country_elem is not None:
                    doc_id = country_elem.text + doc_num_elem.text
                    
                    if doc_id not in seen_ids:
                        # 2. Titel suchen (dieser steht im selben übergeordneten Block 'biblio-ad-search' oder 'item')
                        # Da 'title' oft ein Geschwister-Element ist, suchen wir im 'root' nach der passenden ID
                        title = "Patent-Anmeldung" # Standardwert
                        
                        # Suche das Datum
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
            print(f"Fehler bei Firma {firma}: {e}")




    # 4. Speichern (immer ausführen, damit Git keinen Fehler wirft)
    all_patents.sort(key=lambda x: x.get('datum', '0000'), reverse=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_patents, f, indent=4, ensure_ascii=False)
    
    if new_found:
        print(f"Update erfolgreich: Neue Patente gefunden.")
    else:
        print("Keine neuen Patente gefunden, Datei wurde dennoch aktualisiert.")


if __name__ == "__main__":
    run_monitor()
