import streamlit as st
import pandas as pd
import requests
import json
import base64

# --- 1. PASSWORT SCHUTZ ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.title("Login")
    password = st.text_input("Bitte Passwort eingeben", type="password")
    if st.button("Einloggen"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Passwort falsch")
    return False

if check_password():
    st.title("🔒 EPO Patent Monitor")
    
    # --- 2. KONFIGURATION ---
    USER = "CommanderSpecialK"
    REPO = "EPO-Patent-Monitor"
    FILE = "app_patent_data.json"
    
    # Status-Anzeige für dich
    status = st.empty()
    status.info("⏳ Verbinde mit GitHub API...")

    # --- 3. DATEN LADEN ---
    try:
        # Prüfen ob Secret vorhanden ist
        if "GH_PAT" not in st.secrets:
            st.error("FEHLER: 'GH_PAT' wurde nicht in den Streamlit Secrets gefunden!")
            st.stop()

        token = st.secrets["GH_PAT"]
        headers = {"Authorization": f"token {token}"}
        API_URL = f"https://api.github.com/repos/{USER}/{REPO}/contents/{FILE}"

        response = requests.get(API_URL, headers=headers)
        
        if response.status_code == 200:
            status.success("✅ Verbindung erfolgreich, verarbeite Daten...")
            
            content_json = response.json()
            base64_content = content_json['content']
            decoded_bytes = base64.b64decode(base64_content)
            decoded_str = decoded_bytes.decode('utf-8')
            
            patent_data = json.loads(decoded_str)
            
            if not patent_data:
                st.info("Die Datenbank ist aktuell leer. Nutze den Update-Button unten.")
            else:
                df = pd.DataFrame(patent_data)
                # Spalten etwas schöner anordnen falls vorhanden
                st.dataframe(df, use_container_width=True)
                status.empty() # Statusmeldung entfernen wenn Daten da sind
                
        elif response.status_code == 404:
            st.error(f"❌ Datei '{FILE}' nicht gefunden. (Status 404)")
            st.info("Hinweis: Prüfe ob dein Token 'repo' Rechte für private Repos hat.")
        else:
            st.error(f"❌ GitHub API Fehler: {response.status_code}")
            st.write(response.text)

    except Exception as e:
        st.error(f"❌ Fehler bei der Verarbeitung: {e}")

    # --- 4. UPDATE BUTTON ---
    st.divider()
    st.subheader("System-Steuerung")
    if st.button("🔄 Neues EPO-Update anstoßen"):
        with st.spinner("Sende Befehl an GitHub Actions..."):
            dispatch_url = f"https://api.github.com{USER}/{REPO}/actions/workflows/main.yml/dispatches"
            res = requests.post(dispatch_url, headers=headers, json={"ref": "main"})
            
            if res.status_code == 204:
                st.success("✅ Update gestartet! Das JSON wird in ca. 2 Min. aktualisiert.")
            else:
                st.error(f"Update-Fehler: {res.status_code}")
                st.write(res.text)
