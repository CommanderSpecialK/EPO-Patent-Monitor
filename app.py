import streamlit as st
import pandas as pd
import requests
import json
import os
import base64

# 1. Passwortschutz
def check_password():
    def password_entered():
        if st.session_state["password"] == "wflentw": # Ändern!
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Passwort eingeben", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]


if check_password():
    st.title("🔒 Interner Patent Monitor")

    # 1. API-Abruf vorbereiten
    # WICHTIG: Ersetze USER und REPO durch deine echten Namen!
    USER = "CommanderSpecialK"
    REPO = "EPO-Patent-Monitor"
    API_URL = f"https://api.github.com/{USER}/{REPO}/contents/app_patent_data.json"
    
    headers = {"Authorization": f"token {st.secrets['GH_PAT']}"}

    try:
        response = requests.get(API_URL, headers=headers)
        
        if response.status_code == 200:
            content_json = response.json()
            
            # GitHub liefert den Inhalt Base64-kodiert im Feld 'content'
            base64_content = content_json['content']
            decoded_bytes = base64.b64decode(base64_content)
            decoded_str = decoded_bytes.decode('utf-8')
            
            # Jetzt haben wir den echten JSON-Text unserer Patent-Liste
            patent_data = json.loads(decoded_str)
            
            if not patent_data:
                st.info("Die Datenbank ist aktuell noch leer. Starte ein Update!")
            else:
                df = pd.DataFrame(patent_data)
                
                # Anzeige verschönern
                st.success(f"{len(df)} Patente gefunden.")
                # Spalten sortieren oder auswählen falls gewünscht
                st.dataframe(df, use_container_width=True)
                
        elif response.status_code == 404:
            st.error("Datei 'app_patent_data.json' nicht im Repo gefunden.")
        else:
            st.error(f"GitHub API Fehler {response.status_code}: {response.text}")

    except Exception as e:
        st.error(f"Fehler bei der Datenverarbeitung: {e}")

    # ... (Update-Button Logik hier drunter)



    # ... (Update Button Logik wie zuvor)


    # 2. Update Button Logik
    if st.button("🔄 Jetzt Daten vom EPA abrufen (GitHub Action)"):
        # Trigger an GitHub senden
        headers = {"Authorization": f"token {st.secrets['GH_PAT']}"}
        url = "https://api.github.com"
        data = {"ref": "main"}
        res = requests.post(url, headers=headers, json=data)
        if res.status_code == 204:
            st.success("Update-Prozess gestartet! Bitte in 2 Min. Seite neu laden.")
        else:
            st.error(f"Fehler beim Starten: {res.status_code}")

    # 3. Daten laden & anzeigen
    # Nutze st.secrets für die URL, falls das Repo privat ist
    DATA_URL = "https://raw.githubusercontent.com"
    # Da das Repo privat ist, brauchen wir auch hier den Token im Header
    headers = {"Authorization": f"token {st.secrets['GH_PAT']}"}
    
    response = requests.get(DATA_URL, headers=headers)
    if response.status_code == 200:
        df = pd.DataFrame(json.loads(response.text))
        st.dataframe(df)
    else:
        st.warning("Noch keine Daten vorhanden oder Token ungültig.")
