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

# ... (Oben: Imports und Passwort-Check)

if check_password():
    st.title("🔒 Interner Patent Monitor")

    # Zugriff auf GitHub via Secret Token
    # Stelle sicher, dass GH_PAT in den Streamlit Cloud Secrets hinterlegt ist!
    token = st.secrets["GH_PAT"]
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.raw" # Erzwingt den Rohinhalt via API
    }
    
    # URL zum RAW-Inhalt (achte auf das /main/ oder /master/)
    API_URL = "https://api.github.com"

    try:
        response = requests.get(API_URL, headers=headers)
        
        if response.status_code == 200:
            # Die API liefert bei diesem Header direkt den Dateiinhalt
            data = response.json() 
            df = pd.DataFrame(data)
            st.success("Daten geladen!")
            st.dataframe(df)
        else:
            st.error(f"Fehler {response.status_code}: Wahrscheinlich ist der GH_PAT nicht korrekt oder die URL falsch.")
            st.write("Antwort von GitHub:", response.text[:200]) # Hilft beim Debuggen
    except Exception as e:
        st.error(f"Fehler: {e}")


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
