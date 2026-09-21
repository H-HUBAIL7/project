import contextlib
import io
import unittest

from app.database import SessionLocal
from app.seed import build

_built = False


def ensure_database() -> None:
    global _built
    if not _built:
        with contextlib.redirect_stdout(io.StringIO()):
            build()
        _built = True


class DatabaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_database()

    def setUp(self) -> None:
        self.session = SessionLocal()

    def tearDown(self) -> None:
        self.session.rollback()
        self.session.close()
