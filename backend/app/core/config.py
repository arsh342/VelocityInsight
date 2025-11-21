from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import os


class Settings(BaseModel):
    # Use a default path if DATASET_ROOT is not set
    dataset_root: Path = Path(os.getenv("DATASET_ROOT", "./data")).resolve()
    default_track: str = os.getenv("DEFAULT_TRACK", "barber")
    default_race: str = os.getenv("DEFAULT_RACE", "R1")
    # Make gemini_api_key optional to prevent crashes when not set
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    class Config:
        arbitrary_types_allowed = True


settings = Settings()
