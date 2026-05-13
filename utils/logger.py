import logging, sys
from pathlib import Path
from datetime import datetime

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"assistant_{datetime.now().strftime('%Y%m%d')}.log"
_done = False

def get_logger(name: str) -> logging.Logger:
    global _done
    if not _done:
        fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", "%H:%M:%S")
        ch = logging.StreamHandler(sys.stdout); ch.setLevel(logging.INFO); ch.setFormatter(fmt)
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8"); fh.setLevel(logging.DEBUG); fh.setFormatter(fmt)
        r = logging.getLogger(); r.setLevel(logging.DEBUG); r.addHandler(ch); r.addHandler(fh)
        _done = True
    return logging.getLogger(name)
