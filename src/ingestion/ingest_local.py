import sys
import os
import cv2
import chromadb
import torch
from PIL import Image
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.processing.vibe_check import get_image_embedding

# --- CONFIGURATION ---
VIDEO_FOLDER = "data/video_clips"
SAMPLE_INTERVAL = 4  # Analyze 1 frame every 4 seconds (Good balance of speed vs. detail)
SKIP_EXTENSIONS = ['.part', '.jpg', '.png']

def process_video(filepath, collection):
    filename = os.path.basename(filepath)
    print(f"\n🎥 Scanning: {filename}")
    
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        print(f"❌ Error: Could not open {filename}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    # Calculate how many frames we will extract
    timestamps = list(range(0, int(duration), SAMPLE_INTERVAL))
    
    # Batch processing loop with Progress Bar
    success_count = 0
    
    for current_time in tqdm.tqdm(timestamps, desc="Indexing Game", unit="clips"):
        # Jump specifically to this timestamp (ms)
        cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
        ret, frame = cap.read()
        
        if not ret:
            continue
            
        # Unique ID: filename + timestamp
        # e.g. "Maryland_vs_UConn_1204" (1204 seconds in)
        clip_id = f"{filename}_{current_time}"
        
        # Convert BGR (OpenCV) to RGB (AI expects RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        
        # --- AI MAGIC HAPPENS HERE ---
        # The 'get_image_embedding' function uses your GPU if available
        try:
            vector = get_image_embedding(pil_image)
            
            # Save to Database
            collection.add(
                ids=[clip_id],
                embeddings=[vector],
                metadatas=[{
                    "source_video": filename,
                    "timestamp": current_time,
                    "description": f"Game Action at {current_time}s"
                }]
            )
            success_count += 1
        except Exception as e:
            print(f"Error indexing frame: {e}")

    cap.release()
    print(f"✅ Indexed {success_count} searchable moments from this game.")

def run_local_ingestion():
    # 0. Hardware Check
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"⚙️  Hardware: {device.upper()} (NVIDIA {'Enabled' if device == 'cuda' else 'Not Found'})")

    # 1. Setup Database
    db_path = os.path.join(os.getcwd(), "data/vector_db")
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_or_create_collection(name="skout_plays")

    # 2. Find Files
    video_files = [
        f for f in os.listdir(VIDEO_FOLDER) 
        if f.endswith('.mp4') and not any(f.endswith(ext) for ext in SKIP_EXTENSIONS)
    ]
    
    print(f"found {len(video_files)} full games to process.")

    # 3. Process Each Game
    for video in video_files:
        full_path = os.path.join(VIDEO_FOLDER, video)
        process_video(full_path, collection)

if __name__ == "__main__":
    # Install tqdm if missing for the progress bar
    try:
        import tqdm
    except ImportError:
        os.system('pip install tqdm')
        
    run_local_ingestion()
