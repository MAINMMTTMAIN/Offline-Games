import os
import urllib.request
import zipfile
import subprocess
import sys

def setup():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "games", "chess_game", "assets")
    pieces_dir = os.path.join(assets_dir, "pieces")
    
    os.makedirs(pieces_dir, exist_ok=True)
    
    # 1. Download Pieces from chess.com
    pieces = ['wp', 'wn', 'wb', 'wr', 'wq', 'wk', 'bp', 'bn', 'bb', 'br', 'bq', 'bk']
    print("Downloading chess pieces...")
    for p in pieces:
        url = f"https://images.chesscomfiles.com/chess-themes/pieces/neo/150/{p}.png"
        file_path = os.path.join(pieces_dir, f"{p}.png")
        if not os.path.exists(file_path):
            try:
                urllib.request.urlretrieve(url, file_path)
                print(f"Downloaded {p}.png")
            except Exception as e:
                print(f"Failed to download {p}.png: {e}")
                
    # 2. Download Stockfish
    print("Downloading Stockfish...")
    sf_zip = os.path.join(assets_dir, "stockfish.zip")
    sf_dir = os.path.join(assets_dir, "stockfish")
    sf_exe_dest = os.path.join(assets_dir, "stockfish.exe")
    
    if not os.path.exists(sf_exe_dest):
        url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-windows-x86-64.zip"
        urllib.request.urlretrieve(url, sf_zip)
        print("Stockfish downloaded, extracting...")
        with zipfile.ZipFile(sf_zip, 'r') as zip_ref:
            zip_ref.extractall(sf_dir)
            
        # Find the exe inside the extracted folder
        for root, dirs, files in os.walk(sf_dir):
            for file in files:
                if file.endswith(".exe"):
                    os.rename(os.path.join(root, file), sf_exe_dest)
                    break
        
        # Cleanup
        try:
            os.remove(sf_zip)
        except:
            pass
        print("Stockfish setup complete.")
    else:
        print("Stockfish already exists.")
        
    # 3. Install stockfish python package
    print("Installing python stockfish wrapper...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "stockfish", "chess"])
    
    print("Setup completed successfully.")

if __name__ == "__main__":
    setup()
