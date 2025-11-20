from pathlib import Path
from pydantic import BaseModel
import os


class Settings(BaseModel):
    dataset_root: Path = Path(os.getenv("DATASET_ROOT")).resolve()
    default_track: str = os.getenv("DEFAULT_TRACK", "barber")
    default_race: str = os.getenv("DEFAULT_RACE", "R1")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY")


settings = Settings()
