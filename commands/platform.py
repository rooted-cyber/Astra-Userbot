# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# This file is a PROXY to avoid shadowing the standard library 'platform' module.
# -----------------------------------------------------------

import sys
import os

# Find the standard library platform module by temporarily removing the current directory from sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
original_path = sys.path[:]
if current_dir in sys.path:
    # Remove both the directory and its parent if needed, but usually just current_dir is enough
    sys.path = [p for p in sys.path if os.path.abspath(p) != current_dir]

try:
    import platform as _real_platform
finally:
    sys.path = original_path

# Export everything from the real platform module
globals().update({k: v for k, v in _real_platform.__dict__.items()})

# Note: The original .platform command logic has been moved to sys_info.py
