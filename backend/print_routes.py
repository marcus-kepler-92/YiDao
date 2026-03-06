import sys
from pathlib import Path

sys.path.append(str(Path.cwd()))

from app.main import app

print("Registered Routes:")
for route in app.routes:
    if hasattr(route, "path"):
        print(f"{route.methods} {route.path}")
    else:
        print(route)
