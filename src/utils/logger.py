import logging
import sys

def setup_logger(name="shorts_automation", level=logging.INFO):
    """Configure and return a styled console logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()

def log_step(step_num: int, title: str):
    """Log a prominent step header."""
    logger.info(f"\n{'='*60}\n[Step {step_num}] {title.upper()}\n{'='*60}")
