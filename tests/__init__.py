import atexit
import os
import tempfile

_handle, _path = tempfile.mkstemp(prefix="records_test_", suffix=".db")
os.close(_handle)
os.environ["DATABASE_URL"] = f"sqlite:///{_path}"


@atexit.register
def _cleanup() -> None:
    try:
        from app.database import engine

        engine.dispose()
        os.remove(_path)
    except OSError:
        pass
