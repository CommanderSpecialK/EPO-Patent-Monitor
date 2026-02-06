import streamlit as st
import pandas as pd
import requests
import json
import os

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
    headers = {"Authorization": f"token {token}"}
    
    # URL zum RAW-Inhalt (achte auf das /main/ oder /master/)
    DATA_URL = "https://raw.githubusercontent.com"

    try:
        response = requests.get(DATA_URL, headers=headers)
        
        if response.status_code == 200:
            content = response.text.strip()
            # Falls die Datei nur "[]" enthält oder leer ist
            if content == "[]" or not content:
                st.info("Die Datenbank ist aktuell noch leer.")
            else:
                # Hier nutzen wir response.json() statt json.loads()
                data = response.json()
                df = pd.DataFrame(data)
                st.success("Daten erfolgreich geladen.")
                st.dataframe(df)
        else:
            st.error(f"GitHub meldet Fehler {response.status_code}. Token oder URL prüfen.")
    except Exception as e:
        st.error(f"Inhalt der Datei ist kein gültiges JSON: {e}")
        # Debug: Zeige die ersten 100 Zeichen der Antwort
        st.code(response.text[:100], language="text")


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
