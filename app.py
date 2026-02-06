import streamlit as st
import pandas as pd
import requests
import json
import base64

# --- KONFIGURATION ---
USER = "CommanderSpecialK"
REPO = "EPO-Patent-Monitor"
FILE = "app_patent_data.json"
API_URL = f"https://api.github.com/repos/{USER}/{REPO}/contents/{FILE}"
headers = {"Authorization": f"token {st.secrets['GH_PAT']}"}

def load_github_data():
    res = requests.get(API_URL, headers=headers)
    if res.status_code == 200:
        content = res.json()
        decoded = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(decoded), content['sha']
    return [], None

def save_github_data(data, sha):
    updated_content = base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8')
    payload = {"message": "Patent gelöscht", "content": updated_content, "sha": sha}
    requests.put(API_URL, headers=headers, json=payload)

# --- UI ---
st.set_page_config(page_title="Patent Manager", layout="wide")
st.title("📂 Firmen-Patent-Manager")

if "patent_list" not in st.session_state:
    data, sha = load_github_data()
    st.session_state.patent_list = data
    st.session_state.sha = sha

# Firmen-Ordner Struktur
firmen = sorted(list(set(p['firma'] for p in st.session_state.patent_list)))

for firma in firmen:
    with st.expander(f"📁 Firma: {firma}", expanded=True):
        # Patente dieser Firma filtern
        f_patents = [p for p in st.session_state.patent_list if p['firma'] == firma]
        
        for p in f_patents:
            col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
            
            with col1:
                st.markdown(f"**{p['titel']}**")
                st.caption(f"ID: {p['id']} | Datum: {p['datum']}")
            
            with col2:
                # Anklickbarer Link als Button-Ersatz
                st.link_button("🌐 Espacenet", p['url'])
            
            with col3:
                # Löschen Button
                if st.button("🗑️ Löschen", key=f"del_{p['id']}"):
                    st.session_state.patent_list.remove(p)
                    save_github_data(st.session_state.patent_list, st.session_state.sha)
                    st.rerun()

st.divider()
if st.button("🔄 Globales EPO-Update anstoßen"):
    dispatch_url = f"https://api.github.com/repos/{USER}/{REPO}/actions/workflows/main.yml/dispatches"
    requests.post(dispatch_url, headers=headers, json={"ref": "main"})
    st.success("Update gestartet!")
