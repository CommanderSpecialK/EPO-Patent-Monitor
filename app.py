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

if check_password():
    st.title("🔒 Interner Patent Monitor")

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
