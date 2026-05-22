import shutil
import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException
from backend.config import settings

router = APIRouter()

@router.post("")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload one or more files and return their saved paths."""
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []
    
    for file in files:
        if not file.filename:
            continue
        
        # Generate a unique filename to avoid collisions
        ext = Path(file.filename).suffix
        filename = f"{uuid.uuid4()}{ext}"
        dest = upload_dir / filename
        
        try:
            with dest.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_paths.append(filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not save file {file.filename}: {str(e)}")
            
    return {"paths": saved_paths}
