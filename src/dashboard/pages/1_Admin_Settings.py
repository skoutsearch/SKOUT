import streamlit as st
import os
import sys
import subprocess
from dotenv import load_dotenv

# Add project root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '../../../'))
sys.path.append(PROJECT_ROOT)

st.set_page_config(page_title="PortalRecruit Admin", layout="wide", page_icon="⚙️")

ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

def save_local_api_key(key):
    """Writes the API key to the .env file (Local Dev Only)."""
    with open(ENV_PATH, "w") as f:
        f.write(f"SYNERGY_API_KEY={key}\n")
    os.environ["SYNERGY_API_KEY"] = key 
    st.toast("API Key Saved Locally!", icon="✅")

def run_ingestion_script(script_name):
    """Runs a python script as a subprocess."""
    script_path = os.path.join(PROJECT_ROOT, "src", script_name)
    try:
        # We pass the current environment to the subprocess so it inherits secrets/env vars
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, env=os.environ)
        return result.stdout + "\n" + result.stderr
    except Exception as e:
        return str(e)

# --- LOAD SECRETS ---
# 1. Try Streamlit Cloud Secrets
cloud_key = st.secrets.get("SYNERGY_API_KEY", None)

# 2. Try Local .env
if not cloud_key:
    load_dotenv(ENV_PATH)
    local_key = os.getenv("SYNERGY_API_KEY", "")
else:
    local_key = cloud_key

st.title("⚙️ System Configuration")
st.markdown("Manage your Synergy Data connection and database status.")

# --- SECTION 1: API CREDENTIALS ---
st.subheader("1. Synergy API Connection")

if cloud_key:
    st.success("✅ Connected via Streamlit Cloud Secrets (Read-Only)")
    st.info("To change this key, update your settings in the Streamlit Cloud dashboard.")
else:
    with st.form("api_key_form"):
        user_key = st.text_input("Enter Synergy API Key", value=local_key, type="password")
        submit = st.form_submit_button("Save Credentials")
        
        if submit:
            save_local_api_key(user_key)
            st.rerun()

st.divider()

# --- SECTION 2: DATA INGESTION ---
st.subheader("2. Data Pipeline")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Step 1: Game Schedule**")
    st.info("Fetches latest games from API.")
    if st.button("Sync Schedule"):
        with st.spinner("Fetching games..."):
            log = run_ingestion_script("ingestion/ingest_acc_schedule.py")
            st.text_area("Log", log, height=150)

with col2:
    st.markdown("**Step 2: Play Data**")
    st.info("Downloads PBP data for games.")
    if st.button("Sync Plays"):
        with st.spinner("Downloading plays..."):
            log = run_ingestion_script("ingestion/ingest_game_events.py")
            st.text_area("Log", log, height=150)

with col3:
    st.markdown("**Step 3: AI Intelligence**")
    st.info("Generates Tags & Embeddings.")
    if st.button("Build AI Index"):
        with st.spinner("Thinking..."):
            # Run Tagger then Embeddings
            log1 = run_ingestion_script("processing/apply_tags.py")
            log2 = run_ingestion_script("processing/generate_embeddings.py")
            st.text_area("Log", log1 + "\n" + log2, height=150)
