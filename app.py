import streamlit as st
import pandas as pd
import requests
import json
import base64

# --- 1. PASSWORT SCHUTZ ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "DEIN_WUNSCHPASSWORT": # HIER PASSWORT ÄNDERN
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Passwort", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

if check_password():
    st.title("🔒 EPO Patent Monitor")

    # --- 2. KONFIGURATION ---
    # WICHTIG: Prüfe diese Namen exakt!
    USER = "CommanderSpecialK"
    REPO = "EPO-Patent-Monitor"
    FILE = "app_patent_data.json"
    
    # API URL
    API_URL = f"https://api.github.com{USER}/{REPO}/contents/{FILE}"
    
    # Header mit Token aus den Streamlit Secrets
    headers = {"Authorization": f"token {st.secrets['GH_PAT']}"}

    # --- 3. DATEN LADEN ---
    try:
        response = requests.get(API_URL, headers=headers)
        
        if response.status_code == 200:
            content_json = response.json()
            # GitHub kodiert Dateiinhalte in Base64
            base64_content = content_json['content']
            decoded_bytes = base64.b64decode(base64_content)
            decoded_str = decoded_bytes.decode('utf-8')
            
            patent_data = json.loads(decoded_str)
            
            if not patent_data:
                st.info("Die Datenbank ist aktuell leer.")
            else:
                df = pd.DataFrame(patent_data)
                st.success(f"{len(df)} Patente geladen.")
                st.dataframe(df, use_container_width=True)
                
        elif response.status_code == 404:
            st.error(f"Datei '{FILE}' wurde im Repository nicht gefunden. Prüfe den Dateinamen!")
        else:
            st.error(f"GitHub API Fehler {response.status_code}")
            st.write(response.text)

    except Exception as e:
        st.error(f"Fehler bei der Verarbeitung: {e}")

    # --- 4. UPDATE BUTTON ---
    st.divider()
    if st.button("🔄 Jetzt EPO-Update starten"):
        # Trigger für GitHub Action
        dispatch_url = f"https://api.github.com{USER}/{REPO}/actions/workflows/main.yml/dispatches"
        dispatch_data = {"ref": "main"}
        
        res = requests.post(dispatch_url, headers=headers, json=dispatch_data)
        if res.status_code == 204:
            st.success("Update angestoßen! Das dauert ca. 1-2 Minuten. Bitte Seite später neu laden.")
        else:
            st.error(f"Update fehlgeschlagen: {res.status_code}")
            st.write(res.text)
