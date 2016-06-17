import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Update search path to include repository root
sys.path.insert(0, os.path.abspath(os.path.join(CURRENT_DIR, '..', '..')))
