"""Atomic writes for local, unpublished workflow outputs."""

from contextlib import contextmanager
from pathlib import Path
import os
import tempfile


@contextmanager
def atomic_text(path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                         delete=False) as stream:
            temporary = stream.name
            yield stream
        os.replace(temporary, target)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
