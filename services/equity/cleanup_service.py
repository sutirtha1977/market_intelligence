import os
import traceback
from config.logger import log

# --------------------------------------------------------------------------
def delete_files_in_folder(folder_path: str) -> int:
    if not folder_path or not isinstance(folder_path, str):
        raise ValueError(f"Invalid folder_path: {folder_path}") 
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder does not exist: {folder_path}")
    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"Path is not a directory: {folder_path}")
    deleted: int = 0
    try:
        for filename in os.listdir(folder_path):
            filepath: str = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    deleted += 1
            except OSError as e:
                log(f"⚠️ Failed to delete {filename}: {e}")
        
        log(f"✅ Deleted {deleted} files from: {folder_path}")
        return deleted
    except Exception as e:
        log(f"❌ Failed to delete files from {folder_path}: {e}")
        traceback.print_exc()
        raise
# --------------------------------------------------------------------------