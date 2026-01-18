import streamlit as st
import chromadb
import os
import sys
import torch
from transformers import CLIPProcessor, CLIPModel

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

st.set_page_config(page_title="SKOUT Local", layout="wide")
DB_PATH = os.path.join(os.getcwd(), "data/vector_db")
VIDEO_ROOT = os.path.join(os.getcwd(), "data/video_clips")

# --- CACHED RESOURCES ---
@st.cache_resource
def load_ai_model():
    print("🔄 Loading CLIP Model...")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", use_safetensors=True)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor

@st.cache_resource
def load_db():
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_collection(name="skout_plays")

# --- APP UI ---
st.title("🏀 SKOUT: Local Video Search")

if not os.path.exists(VIDEO_ROOT):
    st.error(f"Video folder not found at: {VIDEO_ROOT}")
    st.stop()

# Load Engine
model, processor = load_ai_model()
collection = load_db()

query = st.text_input("Scout for:", "A slam dunk")

if query:
    st.divider()
    
    # 1. Generate Vector
    inputs = processor(text=[query], return_tensors="pt", padding=True)
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
    search_vec = text_features[0].tolist()

    # 2. Search DB
    results = collection.query(
        query_embeddings=[search_vec],
        n_results=10 # Show top 10 matches
    )

    if results['ids'] and results['ids'][0]:
        for i in range(len(results['ids'][0])):
            meta = results['metadatas'][0][i]
            score = results['distances'][0][i]
            
            video_filename = meta['source_video']
            timestamp = int(meta['timestamp'])
            full_video_path = os.path.join(VIDEO_ROOT, video_filename)

            # 3. Render Result
            with st.container():
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Streamlit video player supports 'start_time'
                    if os.path.exists(full_video_path):
                        st.video(full_video_path, start_time=timestamp)
                    else:
                        st.error(f"Video file missing: {video_filename}")
                        
                with col2:
                    st.subheader(f"Match #{i+1}")
                    st.caption(f"File: {video_filename}")
                    st.caption(f"Time: {timestamp // 60}m {timestamp % 60}s")
                    st.progress(max(0.0, 1.0 - score), text=f"Confidence: {score:.4f}")
                
                st.divider()
    else:
        st.warning("No matches found.")
