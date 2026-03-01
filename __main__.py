"""Atlantis — The Lost Civilization, Rebuilt"""
import sys
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=True)
except ImportError:
    pass

from core.engine import main

if __name__ == "__main__":
    # Forward CLI args (including --demo-electrical) to core.engine.main.
    main(sys.argv[1:])
