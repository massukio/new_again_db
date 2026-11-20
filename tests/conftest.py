import os
import sys
import traceback

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# PyQt5 aborts the whole process when an exception escapes a Qt callback (slot,
# event handler) and no excepthook is set. Record them instead and fail the test.
QT_ERRORS = []


def _hook(exc_type, exc, tb):
    QT_ERRORS.append("".join(traceback.format_exception(exc_type, exc, tb)))


sys.excepthook = _hook


@pytest.fixture(autouse=True)
def no_errors_in_qt_callbacks():
    QT_ERRORS.clear()
    yield
    if QT_ERRORS:
        errors = "\n".join(QT_ERRORS)
        QT_ERRORS.clear()
        pytest.fail(f"exception raised inside a Qt callback:\n{errors}")
