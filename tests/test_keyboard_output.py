import importlib.util
import sys
import types
from pathlib import Path


def load_module():
    keyboard = types.ModuleType("pynput.keyboard")
    keyboard.Controller = object
    keyboard.Key = object
    keyboard.KeyCode = object
    pynput = types.ModuleType("pynput")
    pynput.keyboard = keyboard
    sys.modules.setdefault("pynput", pynput)
    sys.modules.setdefault("pynput.keyboard", keyboard)

    source = Path(__file__).parents[1] / "模拟键盘输入小工具.py"
    spec = importlib.util.spec_from_file_location("keyboard_app_output", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_send_input_controller_emits_unicode_keydown_and_keyup():
    module = load_module()
    controller = module.SendInputController()
    calls = []
    controller._send_input_event = lambda vk, flags, scan=0: calls.append((vk, flags, scan))

    controller.type_char("中", delay=0)

    assert calls == [
        (0, controller.KEYEVENTF_UNICODE, ord("中")),
        (0, controller.KEYEVENTF_UNICODE | controller.KEYEVENTF_KEYUP, ord("中")),
    ]


def test_send_input_controller_emits_ascii_as_unicode_text_input():
    module = load_module()
    controller = module.SendInputController()
    calls = []
    controller._send_input_event = lambda vk, flags, scan=0: calls.append((vk, flags, scan))

    controller.type_char("a", delay=0)

    assert calls == [
        (0, controller.KEYEVENTF_UNICODE, ord("a")),
        (0, controller.KEYEVENTF_UNICODE | controller.KEYEVENTF_KEYUP, ord("a")),
    ]


def test_send_input_controller_raises_when_windows_rejects_input():
    module = load_module()
    controller = module.SendInputController()
    controller._send_input_event = lambda *args: (_ for _ in ()).throw(
        RuntimeError("SendInput returned zero events")
    )

    try:
        controller.type_char("a", delay=0)
    except RuntimeError as error:
        assert "SendInput returned zero events" in str(error)
    else:
        raise AssertionError("a rejected SendInput call must be visible to the caller")


def test_send_input_controller_declares_pointer_argument_without_truncation():
    module = load_module()
    controller = module.SendInputController()

    assert controller._send_input_api.argtypes[1] is __import__("ctypes").c_void_p
