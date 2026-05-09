import ctypes
from ctypes import wintypes
import time
import threading
from tkinter import *
from tkinter import scrolledtext, messagebox, filedialog, ttk
from contextlib import contextmanager

from pynput.keyboard import Controller, Key, KeyCode

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
HOTKEY_ID = 1
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

# ==============================================================================
#  SendInputController: 使用 ctypes 和 SendInput 实现的底层键盘控制器
# ==============================================================================
class SendInputController:
    """
    一个使用 ctypes 调用 Windows SendInput API 的底层键盘模拟器。
    它旨在替代 pynput，以绕过某些软件的检测。
    """
    def __init__(self):
        # 定义Windows API结构体和常量
        self.PUL = ctypes.POINTER(ctypes.c_ulong)
        class KeyBdInput(ctypes.Structure):
            _fields_ = [("wVk", ctypes.c_ushort),
                        ("wScan", ctypes.c_ushort),
                        ("dwFlags", ctypes.c_ulong),
                        ("time", ctypes.c_ulong),
                        ("dwExtraInfo", self.PUL)]
        class HardwareInput(ctypes.Structure):
            _fields_ = [("uMsg", ctypes.c_ulong),
                        ("wParamL", ctypes.c_short),
                        ("wParamH", ctypes.c_ushort)]
        class MouseInput(ctypes.Structure):
            _fields_ = [("dx", ctypes.c_long),
                        ("dy", ctypes.c_long),
                        ("mouseData", ctypes.c_ulong),
                        ("dwFlags", ctypes.c_ulong),
                        ("time", ctypes.c_ulong),
                        ("dwExtraInfo", self.PUL)]
        class Input_I(ctypes.Union):
            _fields_ = [("ki", KeyBdInput),
                        ("mi", MouseInput),
                        ("hi", HardwareInput)]
        class Input(ctypes.Structure):
            _fields_ = [("type", ctypes.c_ulong),
                        ("ii", Input_I)]

        self.Input = Input
        self.KeyBdInput = KeyBdInput
        self.Input_I = Input_I  # 添加这一行，解决 'Input_I' 属性缺失问题
        
        # 定义键盘事件常量
        self.KEYEVENTF_KEYUP = 0x0002
        self.KEYEVENTF_SCANCODE = 0x0008
        self.INPUT_KEYBOARD = 1
        
        # 虚拟键码 (Virtual-Key Codes)
        # 完整的列表可以在微软文档中找到
        self.VK_SHIFT = 0x10
        self.VK_CONTROL = 0x11
        self.VK_ALT = 0x12
        self.VK_RETURN = 0x0D  # Enter
        self.VK_TAB = 0x09
        self.VK_HOME = 0x24
        
        # 字符到虚拟键码和是否需要Shift的映射
        # 这个映射可以根据需要扩展
        self.CHAR_MAP = {
            'a': (0x41, False), 'b': (0x42, False), 'c': (0x43, False), 'd': (0x44, False),
            'e': (0x45, False), 'f': (0x46, False), 'g': (0x47, False), 'h': (0x48, False),
            'i': (0x49, False), 'j': (0x4A, False), 'k': (0x4B, False), 'l': (0x4C, False),
            'm': (0x4D, False), 'n': (0x4E, False), 'o': (0x4F, False), 'p': (0x50, False),
            'q': (0x51, False), 'r': (0x52, False), 's': (0x53, False), 't': (0x54, False),
            'u': (0x55, False), 'v': (0x56, False), 'w': (0x57, False), 'x': (0x58, False),
            'y': (0x59, False), 'z': (0x5A, False),
            'A': (0x41, True), 'B': (0x42, True), 'C': (0x43, True), 'D': (0x44, True),
            'E': (0x45, True), 'F': (0x46, True), 'G': (0x47, True), 'H': (0x48, True),
            'I': (0x49, True), 'J': (0x4A, True), 'K': (0x4B, True), 'L': (0x4C, True),
            'M': (0x4D, True), 'N': (0x4E, True), 'O': (0x4F, True), 'P': (0x50, True),
            'Q': (0x51, True), 'R': (0x52, True), 'S': (0x53, True), 'T': (0x54, True),
            'U': (0x55, True), 'V': (0x56, True), 'W': (0x57, True), 'X': (0x58, True),
            'Y': (0x59, True), 'Z': (0x5A, True),
            '0': (0x30, False), '1': (0x31, False), '2': (0x32, False), '3': (0x33, False),
            '4': (0x34, False), '5': (0x35, False), '6': (0x36, False), '7': (0x37, False),
            '8': (0x38, False), '9': (0x39, False),
            ')': (0x30, True), '!': (0x31, True), '@': (0x32, True), '#': (0x33, True),
            '$': (0x34, True), '%': (0x35, True), '^': (0x36, True), '&': (0x37, True),
            '*': (0x38, True), '(': (0x39, True),
            ' ': (0x20, False), ',': (0xBC, False), '.': (0xBE, False), '/': (0xBF, False),
            ';': (0xBA, False), "'": (0xDE, False), '[': (0xDB, False), ']': (0xDD, False),
            '\\': (0xDC, False), '-': (0xBD, False), '=': (0xBB, False),
            '<': (0xBC, True), '>': (0xBE, True), '?': (0xBF, True), ':': (0xBA, True),
            '"': (0xDE, True), '{': (0xDB, True), '}': (0xDD, True), '|': (0xDC, True),
            '_': (0xBD, True), '+': (0xBB, True),
            '`': (0xC0, False), '~': (0xC0, True),
        }

    def _send_input_event(self, vk, flags):
        """底层的事件发送函数"""
        scan_code = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
        # 如果使用 wScan, dwFlags 要包含 KEYEVENTF_SCANCODE
        # ii = self.Input_I(ki=self.KeyBdInput(0, scan_code, flags | self.KEYEVENTF_SCANCODE, 0, self.PUL(0)))
        
        # 直接使用 wVk 更简单
        # 修复类型错误：将整数0转换为c_ulong后再创建指针
        extra = ctypes.c_ulong(0)
        ii = self.Input_I(ki=self.KeyBdInput(vk, 0, flags, 0, ctypes.pointer(extra)))
        x = self.Input(self.INPUT_KEYBOARD, ii)
        ctypes.windll.user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

    def press_key(self, vk_code):
        """按下指定的虚拟键"""
        self._send_input_event(vk_code, 0)

    def release_key(self, vk_code):
        """释放指定的虚拟键"""
        self._send_input_event(vk_code, self.KEYEVENTF_KEYUP)

    def type_key(self, vk_code, delay=0.01):
        """完整地敲击一次指定的虚拟键（按下后释放）"""
        self.press_key(vk_code)
        time.sleep(delay)
        self.release_key(vk_code)

    def type_char(self, char, delay=0.01):
        """输入一个字符，能自动处理Shift键"""
        if char in self.CHAR_MAP:
            vk_code, needs_shift = self.CHAR_MAP[char]
            if needs_shift:
                self.press_key(self.VK_SHIFT)
                time.sleep(delay)
                self.type_key(vk_code, delay)
                time.sleep(delay)
                self.release_key(self.VK_SHIFT)
            else:
                self.type_key(vk_code, delay)
        # 对于不在映射表中的特殊字符，可以添加更多处理逻辑
        # else:
        #     print(f"Warning: Character '{char}' not in map.")

    @contextmanager
    def pressed(self, *vk_codes):
        """
        一个上下文管理器，用于模拟按住一个或多个键。
        完美替代 pynput 的 with keyboard.pressed(...) 写法。
        """
        for code in vk_codes:
            self.press_key(code)
        try:
            yield
        finally:
            # 以相反的顺序释放按键
            for code in reversed(vk_codes):
                self.release_key(code)


# ==============================================================================
#  KeyboardSimulator: 主应用界面和逻辑 (几乎无改动)
# ==============================================================================
class KeyboardSimulator:
    HOTKEY_MODIFIERS = {
        "ctrl": (MOD_CONTROL, "Ctrl", 0x11),
        "control": (MOD_CONTROL, "Ctrl", 0x11),
        "alt": (MOD_ALT, "Alt", 0x12),
        "shift": (MOD_SHIFT, "Shift", 0x10),
        "win": (MOD_WIN, "Win", 0x5B),
        "windows": (MOD_WIN, "Win", 0x5B),
        "meta": (MOD_WIN, "Win", 0x5B),
    }
    HOTKEY_MODIFIER_ORDER = (
        (MOD_CONTROL, "Ctrl", 0x11),
        (MOD_ALT, "Alt", 0x12),
        (MOD_SHIFT, "Shift", 0x10),
        (MOD_WIN, "Win", 0x5B),
    )
    HOTKEY_SPECIAL_KEYS = {
        "enter": (0x0D, "Enter"),
        "return": (0x0D, "Enter"),
        "tab": (0x09, "Tab"),
        "space": (0x20, "Space"),
        "esc": (0x1B, "Esc"),
        "escape": (0x1B, "Esc"),
        "home": (0x24, "Home"),
        "end": (0x23, "End"),
        "pageup": (0x21, "PageUp"),
        "pgup": (0x21, "PageUp"),
        "pagedown": (0x22, "PageDown"),
        "pgdn": (0x22, "PageDown"),
        "insert": (0x2D, "Insert"),
        "ins": (0x2D, "Insert"),
        "delete": (0x2E, "Delete"),
        "del": (0x2E, "Delete"),
        "up": (0x26, "Up"),
        "down": (0x28, "Down"),
        "left": (0x25, "Left"),
        "right": (0x27, "Right"),
        "backspace": (0x08, "Backspace"),
    }

    def __init__(self, window):
        self.window = window
        self.window.configure(bg="#f0f0f0")
        self.window.attributes("-topmost", False)

        main_frame = Frame(window, bg="#f0f0f0")
        main_frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

        # ... (GUI布局代码与原版完全相同，无需修改) ...
        # ---------------- 输入内容区域 ----------------
        input_frame = LabelFrame(main_frame, text="输入内容", padx=10, pady=10, bg="#f0f0f0")
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.text = scrolledtext.ScrolledText(input_frame, wrap=WORD, width=60, height=5, font=("Helvetica", 12))
        self.text.pack(expand=True, fill=BOTH, padx=5, pady=5)

        # ---------------- 参数设置区域 ----------------
        params_frame = LabelFrame(main_frame, text="参数设置", padx=10, pady=10, bg="#f0f0f0")
        params_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # ----- 起始延时设置 -----
        delay_frame = Frame(params_frame, bg="#f0f0f0")
        delay_frame.pack(fill="x", pady=5)

        ttk.Label(delay_frame, text="开始输入的延迟 (秒):", width=25, anchor='w', background="#f0f0f0").pack(
            side=LEFT, padx=(0, 5)
        )
        self.delay_var = DoubleVar(value=2)
        self.scale_delay = ttk.Scale(
            delay_frame, from_=0, to=20, orient=HORIZONTAL,
            variable=self.delay_var, command=self.update_delay_label
        )
        self.scale_delay.pack(side=LEFT, fill="x", expand=True)
        self.delay_label = ttk.Label(
            delay_frame, text=f"{self.delay_var.get():.2f} 秒",
            width=10, anchor='w', background="#f0f0f0"
        )
        self.delay_label.pack(side=LEFT, padx=(5, 0))

        # ----- 输入字符间隔设置 -----
        interval_frame = Frame(params_frame, bg="#f0f0f0")
        interval_frame.pack(fill="x", pady=5)

        ttk.Label(interval_frame, text="输入字符的间隔 (秒):", width=25, anchor='w', background="#f0f0f0").pack(
            side=LEFT, padx=(0, 5)
        )
        self.interval_var = DoubleVar(value=0.05)
        self.scale_interval = ttk.Scale(
            interval_frame, from_=0.01, to=1, orient=HORIZONTAL,
            variable=self.interval_var, command=self.update_interval_label
        )
        self.scale_interval.pack(side=LEFT, fill="x", expand=True)
        self.interval_label = ttk.Label(
            interval_frame, text=f"{self.interval_var.get():.2f} 秒",
            width=10, anchor='w', background="#f0f0f0"
        )
        self.interval_label.pack(side=LEFT, padx=(5, 0))

        # ----- 重复次数设置 -----
        repetition_frame = Frame(params_frame, bg="#f0f0f0")
        repetition_frame.pack(fill="x", pady=5)

        ttk.Label(repetition_frame, text="重复次数:", width=25, anchor='w', background="#f0f0f0").pack(
            side=LEFT, padx=(0, 5)
        )
        self.repetition_entry = ttk.Entry(repetition_frame, width=10)
        self.repetition_entry.pack(side=LEFT, padx=(0, 5))
        self.repetition_entry.insert(0, "1")

        # ----- 开始快捷键设置 -----
        hotkey_frame = Frame(params_frame, bg="#f0f0f0")
        hotkey_frame.pack(fill="x", pady=5)

        ttk.Label(hotkey_frame, text="开始输入快捷键:", width=25, anchor='w', background="#f0f0f0").pack(
            side=LEFT, padx=(0, 5)
        )
        self.hotkey_var = StringVar(value="Ctrl+Alt+S")
        self.hotkey_entry = ttk.Entry(hotkey_frame, width=20, textvariable=self.hotkey_var)
        self.hotkey_entry.pack(side=LEFT, padx=(0, 5))
        self.hotkey_entry.bind("<Return>", self.apply_hotkey)

        self.button_apply_hotkey = ttk.Button(hotkey_frame, text='应用快捷键', command=self.apply_hotkey)
        self.button_apply_hotkey.pack(side=LEFT, padx=(0, 5))

        self.hotkey_status_var = StringVar(value="未注册")
        self.hotkey_status_label = ttk.Label(
            hotkey_frame, textvariable=self.hotkey_status_var,
            width=28, anchor='w', background="#f0f0f0"
        )
        self.hotkey_status_label.pack(side=LEFT, padx=(5, 0))

        # ----- 换行方式下拉框 -----
        newline_mode_frame = Frame(params_frame, bg="#f0f0f0")
        newline_mode_frame.pack(fill="x", pady=5)

        ttk.Label(newline_mode_frame, text="换行方式:", width=25, anchor='w', background="#f0f0f0").pack(
            side=LEFT, padx=(0, 5)
        )

        self.newline_mode_var = StringVar(value="普通使用Enter换行")
        self.newline_options = [
            "普通使用Enter换行", "使用Shift+Enter换行", "换行后10次Shift+Tab", "换行后2次Home回到行首"
        ]

        self.newline_mode_combobox = ttk.Combobox(
            newline_mode_frame, textvariable=self.newline_mode_var, values=self.newline_options, state="readonly", width=20
        )
        self.newline_mode_combobox.current(0)
        self.newline_mode_combobox.pack(side=LEFT, padx=(0, 5))

        # ---------------- 控制按钮区域 ----------------
        controls_frame = Frame(main_frame, bg="#f0f0f0")
        controls_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.topmost_var = BooleanVar(value=False)
        self.topmost_check = ttk.Checkbutton(
            controls_frame, text='窗口始终置顶', variable=self.topmost_var,
            command=self.toggle_topmost, style='TCheckbutton'
        )
        self.topmost_check.pack(side=LEFT, padx=5)

        self.clear_text_var = BooleanVar()
        self.clear_text_checkbutton = ttk.Checkbutton(
            controls_frame, text='执行后清除文本框', variable=self.clear_text_var, style='TCheckbutton'
        )
        self.clear_text_checkbutton.pack(side=LEFT, padx=5)

        self.button_start = ttk.Button(controls_frame, text='开始输入', command=self.simulate_input)
        self.button_start.pack(side=LEFT, padx=5)

        self.button_stop = ttk.Button(controls_frame, text='停止输出', command=self.stop_simulation, state=DISABLED)
        self.button_stop.pack(side=LEFT, padx=5)

        self.button_save = ttk.Button(controls_frame, text='保存记录为TXT文件', command=self.save_records_to_file)
        self.button_save.pack(side=LEFT, padx=5)

        # ---------------- 输出记录区域 ----------------
        records_frame = LabelFrame(main_frame, text="输出记录", padx=10, pady=10, bg="#f0f0f0")
        records_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)

        self.record_text = scrolledtext.ScrolledText(
            records_frame, wrap=WORD, width=60, height=10,
            state=DISABLED, font=("Helvetica", 12)
        )
        self.record_text.pack(expand=True, fill=BOTH, padx=5, pady=5)

        # ---------------- 进度条区域 ----------------
        progress_frame = Frame(main_frame, bg="#f0f0f0")
        progress_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)

        self.progress = ttk.Progressbar(progress_frame, orient=HORIZONTAL, length=500, mode='determinate')
        self.progress.pack(fill="x", expand=True, padx=5, pady=5)

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        self.records = []
        self.stop_event = threading.Event()
        self.input_thread = None
        self.simulation_active = False
        self.hotkey_thread = None
        self.hotkey_thread_id = None
        self.hotkey_ready_event = threading.Event()
        self.hotkey_registration_error = None
        self.current_hotkey_config = None

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.set_styles()
        self.apply_hotkey(show_error=False)
        
    def set_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Microsoft YaHei', 10))
        style.configure('TCheckbutton', font=('Microsoft YaHei', 10))
        style.configure('TLabelframe.Label', font=('Microsoft YaHei', 12, 'bold'))

    def parse_hotkey(self, hotkey_text):
        parts = [part.strip() for part in hotkey_text.split('+') if part.strip()]
        if len(parts) < 2:
            raise ValueError("快捷键至少需要一个修饰键和一个主键，例如 Ctrl+Alt+S。")

        modifiers = 0
        main_vk = None
        main_key_name = None
        release_keys = []
        seen_modifiers = set()

        for part in parts:
            normalized = part.lower()
            if normalized in self.HOTKEY_MODIFIERS:
                modifier_mask, _, modifier_vk = self.HOTKEY_MODIFIERS[normalized]
                if modifier_mask in seen_modifiers:
                    raise ValueError("快捷键中包含重复的修饰键。")
                seen_modifiers.add(modifier_mask)
                modifiers |= modifier_mask
                release_keys.append(modifier_vk)
                continue

            if main_vk is not None:
                raise ValueError("快捷键只能包含一个主键。")

            main_vk, main_key_name = self.parse_hotkey_key(part)

        if modifiers == 0:
            raise ValueError("快捷键至少需要一个修饰键。")
        if main_vk is None:
            raise ValueError("快捷键必须包含一个主键。")

        ordered_parts = [label for mask, label, _ in self.HOTKEY_MODIFIER_ORDER if modifiers & mask]
        ordered_parts.append(main_key_name)
        release_keys.append(main_vk)

        return {
            "text": "+".join(ordered_parts),
            "modifiers": modifiers | MOD_NOREPEAT,
            "vk": main_vk,
            "release_keys": tuple(release_keys),
        }

    def parse_hotkey_key(self, key_text):
        normalized = key_text.strip()
        key_upper = normalized.upper()
        key_lower = normalized.lower()

        if len(key_upper) == 1 and key_upper.isalpha():
            return ord(key_upper), key_upper

        if len(key_upper) == 1 and key_upper.isdigit():
            return ord(key_upper), key_upper

        if key_upper.startswith('F') and key_upper[1:].isdigit():
            index = int(key_upper[1:])
            if 1 <= index <= 24:
                return 0x6F + index, key_upper

        if key_lower in self.HOTKEY_SPECIAL_KEYS:
            return self.HOTKEY_SPECIAL_KEYS[key_lower]

        raise ValueError("主键仅支持单个字母/数字、F1-F24 或常见控制键，例如 Enter、Tab、Home。")

    def apply_hotkey(self, event=None, show_error=True):
        try:
            hotkey_config = self.parse_hotkey(self.hotkey_var.get())
        except ValueError as exc:
            self.hotkey_status_var.set("格式无效")
            if show_error:
                messagebox.showerror("快捷键错误", str(exc))
            return False

        previous_config = self.current_hotkey_config
        if previous_config and previous_config["text"] == hotkey_config["text"] and self.hotkey_thread and self.hotkey_thread.is_alive():
            self.hotkey_var.set(hotkey_config["text"])
            self.hotkey_status_var.set(f"已注册: {hotkey_config['text']}")
            return True

        self.stop_hotkey_listener()
        if self.start_hotkey_listener(hotkey_config):
            self.current_hotkey_config = hotkey_config
            self.hotkey_var.set(hotkey_config["text"])
            self.hotkey_status_var.set(f"已注册: {hotkey_config['text']}")
            return True

        failed_error = self.hotkey_registration_error
        self.stop_hotkey_listener()
        if previous_config and self.start_hotkey_listener(previous_config):
            self.current_hotkey_config = previous_config
            self.hotkey_var.set(previous_config["text"])
            self.hotkey_status_var.set(f"已恢复: {previous_config['text']}")
        else:
            self.current_hotkey_config = None
            self.hotkey_status_var.set("未注册")

        if show_error:
            messagebox.showerror("快捷键错误", f"无法注册快捷键：{self.format_hotkey_error(failed_error)}")
        return False

    def start_hotkey_listener(self, hotkey_config):
        self.hotkey_ready_event = threading.Event()
        self.hotkey_registration_error = None
        self.hotkey_thread = threading.Thread(
            target=self.hotkey_listener_loop,
            args=(hotkey_config["modifiers"], hotkey_config["vk"]),
            daemon=True
        )
        self.hotkey_thread.start()

        if not self.hotkey_ready_event.wait(timeout=2):
            self.hotkey_registration_error = TimeoutError("快捷键注册超时。")
            return False

        return self.hotkey_registration_error is None

    def stop_hotkey_listener(self):
        thread_id = self.hotkey_thread_id
        thread = self.hotkey_thread

        self.hotkey_thread_id = None
        self.hotkey_thread = None

        if thread_id:
            user32.PostThreadMessageW(thread_id, WM_QUIT, 0, 0)

        if thread and thread.is_alive():
            thread.join(timeout=1)

    def hotkey_listener_loop(self, modifiers, vk_code):
        thread_id = kernel32.GetCurrentThreadId()
        self.hotkey_thread_id = thread_id

        if not user32.RegisterHotKey(None, HOTKEY_ID, modifiers, vk_code):
            self.hotkey_registration_error = ctypes.WinError()
            self.hotkey_thread_id = None
            self.hotkey_ready_event.set()
            return

        self.hotkey_registration_error = None
        self.hotkey_ready_event.set()

        msg = wintypes.MSG()
        try:
            while True:
                result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result <= 0:
                    break
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    self.window.after(0, self.start_from_hotkey)
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)
            if self.hotkey_thread_id == thread_id:
                self.hotkey_thread_id = None

    def format_hotkey_error(self, error):
        if error is None:
            return "未知错误。"
        return str(error)

    def start_from_hotkey(self):
        if self.simulation_active:
            return

        release_keys = ()
        if self.current_hotkey_config:
            release_keys = self.current_hotkey_config["release_keys"]
        self.simulate_input(skip_start_delay=True, release_keys=release_keys)

    def release_hotkey_keys(self, keyboard, release_keys):
        for vk_code in reversed(release_keys):
            keyboard.release(KeyCode.from_vk(vk_code))

    def wait_with_stop(self, delay_seconds):
        if delay_seconds <= 0:
            return True

        end_time = time.perf_counter() + delay_seconds
        while not self.stop_event.is_set():
            remaining = end_time - time.perf_counter()
            if remaining <= 0:
                return True
            time.sleep(min(0.05, remaining))
        return False

    def update_delay_label(self, event=None):
        self.delay_label.config(text=f"{self.delay_var.get():.2f} 秒")

    def update_interval_label(self, event=None):
        self.interval_label.config(text=f"{self.interval_var.get():.2f} 秒")

    def toggle_topmost(self):
        self.window.attributes("-topmost", self.topmost_var.get())

    def simulate_input(self, skip_start_delay=False, release_keys=()):
        if self.simulation_active:
            return

        try:
            repetitions = int(self.repetition_entry.get())
            if repetitions < 1: raise ValueError
        except ValueError:
            messagebox.showerror("输入错误", "请提供一个有效的正整数作为重复次数。")
            return

        self.stop_event.clear()
        self.simulation_active = True
        self.button_start.config(state=DISABLED)
        self.button_stop.config(state=NORMAL)

        text_content = self.text.get('1.0', 'end-1c')
        if not text_content.strip():
            messagebox.showwarning("输入警告", "请输入要模拟的内容。")
            self.finish_simulation()
            return
        
        # 回退到旧版 pynput 的实现，以支持中文
        keyboard = Controller()

        start_delay = 0 if skip_start_delay else self.delay_var.get()
        char_delay = self.interval_var.get()
        
        total_chars = repetitions * len(text_content)
        self.progress['maximum'] = total_chars
        self.progress['value'] = 0

        newline_mode = self.newline_mode_var.get()

        def do_newline():
            if newline_mode == "普通使用Enter换行":
                keyboard.press(Key.enter)
                keyboard.release(Key.enter)

            elif newline_mode == "使用Shift+Enter换行":
                with keyboard.pressed(Key.shift):
                    keyboard.press(Key.enter)
                    keyboard.release(Key.enter)

            elif newline_mode == "换行后10次Shift+Tab":
                keyboard.press(Key.enter)
                keyboard.release(Key.enter)
                time.sleep(char_delay)
                for _ in range(10):
                    if self.stop_event.is_set(): break
                    with keyboard.pressed(Key.shift):
                        keyboard.press(Key.tab)
                        keyboard.release(Key.tab)
                    time.sleep(char_delay)

            elif newline_mode == "换行后2次Home回到行首":
                keyboard.press(Key.enter)
                keyboard.release(Key.enter)
                time.sleep(char_delay)
                for _ in range(2):
                    if self.stop_event.is_set(): break
                    keyboard.press(Key.home)
                    keyboard.release(Key.home)
                    time.sleep(char_delay)

        def simulate_input_thread():
            try:
                if not self.wait_with_stop(start_delay):
                    return

                if release_keys:
                    self.release_hotkey_keys(keyboard, release_keys)

                for _ in range(repetitions):
                    if self.stop_event.is_set(): break
                    for char in text_content:
                        if self.stop_event.is_set(): break
                        
                        if char == "\n":
                            do_newline()
                        else:
                            keyboard.type(char)

                        self.window.after(0, self.progress.step, 1)
                        time.sleep(char_delay)

                    if not self.stop_event.is_set():
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                        record_line = f"[{timestamp}] {text_content}"
                        self.records.append(record_line)
                        self.window.after(0, self.update_record_text, record_line)
            finally:
                if self.clear_text_var.get():
                    self.window.after(0, self.text.delete, '1.0', 'end')
                self.window.after(0, self.finish_simulation)

        self.input_thread = threading.Thread(target=simulate_input_thread, daemon=True)
        self.input_thread.start()

    def finish_simulation(self):
        self.simulation_active = False
        self.button_start.config(state=NORMAL)
        self.button_stop.config(state=DISABLED)
        self.progress['value'] = 0

    def stop_simulation(self):
        if not self.simulation_active:
            return
        self.stop_event.set()
        self.button_stop.config(state=DISABLED)
        messagebox.showinfo("停止", "模拟输入已停止。")

    def on_close(self):
        self.stop_event.set()
        self.stop_hotkey_listener()
        self.window.destroy()

    def update_record_text(self, new_entry):
        self.record_text.config(state=NORMAL)
        self.record_text.insert('end', new_entry + '\n')
        self.record_text.see('end')
        self.record_text.config(state=DISABLED)

    def save_records_to_file(self):
        if not self.records:
            messagebox.showwarning("无记录", "没有记录可保存。")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension='.txt', filetypes=[('Text files', '*.txt')], title='保存记录'
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for record in self.records:
                        f.write(record + '\n')
                messagebox.showinfo("成功", f"记录已保存到 {file_path}")
            except Exception as e:
                messagebox.showerror("保存错误", f"无法保存文件：{e}")


if __name__ == "__main__":
    window = Tk()
    window.title('模拟键盘输入 (SendInput底层版)')
    window.geometry('700x600')
    window.minsize(700, 600)

    app = KeyboardSimulator(window)
    window.mainloop()