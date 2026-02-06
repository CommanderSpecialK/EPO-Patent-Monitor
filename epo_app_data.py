import os
import json
import epo_ops
import xml.etree.ElementTree as ET
from datetime import datetime

# Konfiguration
firma = ['WFL Millturn'] 
DATA_FILE = 'app_patent_data.json'

def get_text(element, path, namespaces):
    found = element.find(path, namespaces)
    return found.text if found is not None else ""

def run_monitor():
    client = epo_ops.Client(key=os.environ['EPO_KEY'], secret=os.environ['EPO_SECRET'])
    
    # Bestehende Daten laden (um nur Historie zu behalten)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            all_patents = json.load(f)
    else:
        all_patents = []

    seen_ids = {p['id'] for p in all_patents}
    new_found = False

    namespaces = {
        'ops': 'http://www.epo.org',
        'exchange': 'http://www.epo.org',
        'abstract': 'http://www.epo.org'
    }

    for firma in FIRMEN:
        # Suche nach Anmelder (pa)
        response = client.published_data_search(query=f'pa="{firma}"', range_begin=1, range_end=50)
        root = ET.fromstring(response.content)
        
        for item in root.findall('.//exchange:item', namespaces):
            doc_id = item.get('epodoc-id')
            
            if doc_id not in seen_ids:
                title = get_text(item, './/exchange:title', namespaces)
                date = get_text(item, './/exchange:publication-reference//exchange:date', namespaces)
                
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

    if new_found:
        # Sortieren nach Datum (neueste zuerst)
        all_patents.sort(key=lambda x: x['datum'], reverse=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_patents, f, indent=4, ensure_ascii=False)
        print(f"Update erfolgreich: {DATA_FILE} aktualisiert.")

if __name__ == "__main__":
    run_monitor()
