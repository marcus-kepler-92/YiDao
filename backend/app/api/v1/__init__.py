"""
API v1 Router

Automatically includes all routers from this package.
Add new routers by creating a new file with a `router` variable.
"""

from importlib import import_module
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

# Auto-discover and include routers from this package
_package_path = Path(__file__).parent
_module_files = [
    f.stem
    for f in _package_path.glob("*.py")
    if f.is_file() and f.stem != "__init__" and not f.stem.startswith("_")
]

for module_name in _module_files:
    try:
        module = import_module(f"app.api.v1.{module_name}")
        if hasattr(module, "router"):
            router.include_router(module.router)
    except ImportError as e:
        # Log import errors but don't fail
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to import router from {module_name}: {e}")
    except Exception as e:
        # Log other errors but don't fail (e.g., type checking issues during import)
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"Non-critical error importing {module_name}: {e}")
        # Try to include router anyway if it exists
        try:
            module = import_module(f"app.api.v1.{module_name}")
            if hasattr(module, "router"):
                router.include_router(module.router)
        except Exception:
            pass

__all__ = ["router"]
