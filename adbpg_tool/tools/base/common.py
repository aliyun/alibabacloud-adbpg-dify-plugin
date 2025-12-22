import logging

# Setup logger for tools module with file output
logger = logging.getLogger("adbpg.tools")
logger.setLevel(logging.INFO)

_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# File handler - write to /tmp
_file_handler = logging.FileHandler("/tmp/adbpg_tools.log")
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(_formatter)
logger.addHandler(_file_handler)

# Console handler
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_formatter)
logger.addHandler(_console_handler)
