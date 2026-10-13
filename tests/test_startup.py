import importlib.util
import sys
import types
from pathlib import Path


def load_application_module():
    keyboard = types.ModuleType("pynput.keyboard")
    keyboard.Controller = object
    keyboard.Key = object
    keyboard.KeyCode = object
    pynput = types.ModuleType("pynput")
    pynput.keyboard = keyboard
    sys.modules.setdefault("pynput", pynput)
    sys.modules.setdefault("pynput.keyboard", keyboard)

    root = Path(__file__).parents[1]
    source = root / "模拟键盘输入小工具.py"
    if not source.exists():
        source = root / "simulate_keyboard_input.py"
    spec = importlib.util.spec_from_file_location("simulate_keyboard_input", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_startup_exception_is_reported_without_entering_mainloop():
    module = load_application_module()
    events = []

    class FakeWindow:
        def title(self, _value):
            pass

        def geometry(self, _value):
            pass

        def minsize(self, _width, _height):
            pass

        def destroy(self):
            pass

    def create_app(_window):
        raise RuntimeError("hotkey initialization failed")

    result = module.run_application(
        create_window=FakeWindow,
        create_app=create_app,
        enter_mainloop=lambda: events.append("mainloop"),
        report_error=lambda error: events.append(str(error)),
    )

    assert result is False
    assert events == ["hotkey initialization failed"]

