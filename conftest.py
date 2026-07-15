import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))

if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

_env = os.path.join(RAIZ, ".env")
if not os.path.exists(_env):
    shutil.copy(os.path.join(RAIZ, ".env.example"), _env)
