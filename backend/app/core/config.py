from pathlib import Path
from pydantic import BaseModel
import os


class Settings(BaseModel):
    dataset_root: Path = Path(os.getenv("DATASET_ROOT", "/Users/arsh/Developer/Projects/gr2025/dataset")).resolve()
    default_track: str = os.getenv("DEFAULT_TRACK", "barber")
    default_race: str = os.getenv("DEFAULT_RACE", "R1")


settings = Settings()
