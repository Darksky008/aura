"""Seed the demo hotel:   python seed.py           (idempotent)
                         python seed.py --reset   (drops ALL tables first)"""
import sys

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.session import SessionLocal
from seed.run import seed_demo

if __name__ == "__main__":
    configure_logging(get_settings().log_level)
    reset = "--reset" in sys.argv
    with SessionLocal() as db:
        wrote = seed_demo(db, reset=reset)
    print("Seeded AURELIA GRAND HOTEL / Saffron Terrace (7 dishes)." if wrote else "Demo hotel already present - nothing to do. Use --reset to rebuild.")
