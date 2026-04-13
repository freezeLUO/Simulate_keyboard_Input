import time
import threading
from tkinter import *
from tkinter import scrolledtext, messagebox, filedialog, ttk
from contextlib import contextmanager
from pynput import keyboard
from pynput.keyboard import Key, Controller, Listener


# ==============================================================================
#  MacOSKeyboardController: 使用 pynput 实现的 macOS 键盘控制器
# ==============================================================================
class MacOSKeyboardController:
    """
    一个使用 pynput 库的 macOS 键盘模拟器。
    """
    def __init__(self):
        self.keyboard = Controller()
        
        # 虚拟键码映射（用于兼容原代码）
        self.VK_SHIFT = Key.shift
        self.VK_CONTROL = Key.ctrl
        self.VK_ALT = Key.alt
        self.VK_RETURN = Key.enter
        self.VK_TAB = Key.tab
        self.VK_HOME = Key.home
        self.VK_ESCAPE = Key.esc
        self.VK_PAGE_UP = Key.page_up
        self.VK_PAGE_DOWN = Key.page_down
        self.VK_END = Key.end
        self.VK_DELETE = Key.delete
        self.VK_BACKSPACE = Key.backspace
        self.VK_UP = Key.up
        self.VK_DOWN = Key.down
        self.VK_LEFT = Key.left
        self.VK_RIGHT = Key.right
        
        # 字符映射（主要用于特殊字符）
        self.CHAR_MAP = {
            ' ': ' ', ',': ',', '.': '.', '/': '/',
            ';': ';', "'": "'", '[': '[', ']': ']',
            '\\': '\\', '-': '-', '=': '=',
            '<': (',', True), '>': ('.', True), '?': ('/', True), ':': (';', True),
            '"': ("'", True), '{': ('[', True), '}': (']', True), '|': ('\\', True),
            '_': ('-', True), '+': ('=', True),
            '`': '`', '~': ('`', True),
        }

    def press_key(self, key):
        """按下指定的键"""
        self.keyboard.press(key)

    def release_key(self, key):
        """释放指定的键"""
        self.keyboard.release(key)

    def type_key(self, key, delay=0.01):
        """完整地敲击一次指定的键（按下后释放）"""
        self.press_key(key)
        time.sleep(delay)
        self.release_key(key)

    def type_char(self, char, delay=0.01):
        """输入一个字符，能自动处理Shift键"""
        # 直接使用 keyboard.type 方法，它会自动处理字符输入
        # 包括特殊字符和需要Shift的情况
        self.keyboard.type(char)
        time.sleep(delay)

    @contextmanager
    def pressed(self, *keys):
        """
        一个上下文管理器，用于模拟按住一个或多个键。
        """
        for key in keys:
            self.press_key(key)
        try:
            yield
        finally:
            # 以相反的顺序释放按键
            for key in reversed(keys):
                self.release_key(key)


# ==============================================================================
#  KeyboardSimulator: 主应用界面和逻辑
# ==============================================================================
class KeyboardSimulator:
    HOTKEY_MODIFIERS = {
        "ctrl": (Key.ctrl, "Ctrl"),
        "control": (Key.ctrl, "Ctrl"),
        "alt": (Key.alt, "Option"),
        "option": (Key.alt, "Option"),
        "shift": (Key.shift, "Shift"),
        "cmd": (Key.cmd, "Cmd"),
        "command": (Key.cmd, "Cmd"),
        "meta": (Key.cmd, "Cmd"),
    }
    HOTKEY_MODIFIER_ORDER = (
        (Key.ctrl, "Ctrl"),
        (Key.alt, "Option"),
        (Key.shift, "Shift"),
        (Key.cmd, "Cmd"),
    )
    HOTKEY_SPECIAL_KEYS = {
        "enter": (Key.enter, "Enter"),
        "return": (Key.enter, "Enter"),
        "tab": (Key.tab, "Tab"),
        "space": (Key.space, "Space"),
        "esc": (Key.esc, "Esc"),
        "escape": (Key.esc, "Esc"),
        "home": (Key.home, "Home"),
        "end": (Key.end, "End"),
        "pageup": (Key.page_up, "PageUp"),
        "pgup": (Key.page_up, "PageUp"),
        "pagedown": (Key.page_down, "PageDown"),
        "pgdn": (Key.page_down, "PageDown"),
        "delete": (Key.delete, "Delete"),
        "del": (Key.delete, "Delete"),
        "up": (Key.up, "Up"),
        "down": (Key.down, "Down"),
        "left": (Key.left, "Left"),
        "right": (Key.right, "Right"),
        "backspace": (Key.backspace, "Backspace"),
    }

    def __init__(self, window):
        self.window = window
        self.window.configure(bg="#f0f0f0")
        self.window.attributes("-topmost", False)

        main_frame = Frame(window, bg="#f0f0f0")
        main_frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

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
        self.hotkey_var = StringVar(value="Cmd+Option+S")
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
        self.hotkey_listener = None
        self.current_hotkey_config = None

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.set_styles()
        self.apply_hotkey(show_error=False)
        
    def set_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 10))
        style.configure('TCheckbutton', font=('Helvetica', 10))
        style.configure('TLabelframe.Label', font=('Helvetica', 12, 'bold'))

    def parse_hotkey(self, hotkey_text):
        parts = [part.strip() for part in hotkey_text.split('+') if part.strip()]
        if len(parts) < 2:
            raise ValueError("快捷键至少需要一个修饰键和一个主键，例如 Cmd+Alt+S。")

        modifiers = []
        main_key = None
        main_key_name = None
        release_keys = []
        seen_modifiers = set()

        for part in parts:
            normalized = part.lower()
            if normalized in self.HOTKEY_MODIFIERS:
                modifier_key, modifier_label = self.HOTKEY_MODIFIERS[normalized]
                if modifier_key in seen_modifiers:
                    raise ValueError("快捷键中包含重复的修饰键。")
                seen_modifiers.add(modifier_key)
                modifiers.append(modifier_key)
                release_keys.append(modifier_key)
                continue

            if main_key is not None:
                raise ValueError("快捷键只能包含一个主键。")

            main_key, main_key_name = self.parse_hotkey_key(part)

        if not modifiers:
            raise ValueError("快捷键至少需要一个修饰键。")
        if main_key is None:
            raise ValueError("快捷键必须包含一个主键。")

        ordered_parts = [label for key, label in self.HOTKEY_MODIFIER_ORDER if key in seen_modifiers]
        ordered_parts.append(main_key_name)
        release_keys.append(main_key)

        return {
            "text": "+".join(ordered_parts),
            "modifiers": modifiers,
            "key": main_key,
            "release_keys": tuple(release_keys),
        }

    def parse_hotkey_key(self, key_text):
        normalized = key_text.strip()
        key_upper = normalized.upper()
        key_lower = normalized.lower()

        if len(key_upper) == 1 and key_upper.isalpha():
            return key_upper, key_upper

        if len(key_upper) == 1 and key_upper.isdigit():
            return key_upper, key_upper

        if key_upper.startswith('F') and key_upper[1:].isdigit():
            index = int(key_upper[1:])
            if 1 <= index <= 24:
                f_key = getattr(Key, f'f{index}', None)
                if f_key:
                    return f_key, key_upper

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
        if previous_config and previous_config["text"] == hotkey_config["text"] and self.hotkey_listener:
            self.hotkey_var.set(hotkey_config["text"])
            self.hotkey_status_var.set(f"已注册: {hotkey_config['text']}")
            return True

        self.stop_hotkey_listener()
        if self.start_hotkey_listener(hotkey_config):
            self.current_hotkey_config = hotkey_config
            self.hotkey_var.set(hotkey_config["text"])
            self.hotkey_status_var.set(f"已注册: {hotkey_config['text']}")
            return True

        self.stop_hotkey_listener()
        if previous_config and self.start_hotkey_listener(previous_config):
            self.current_hotkey_config = previous_config
            self.hotkey_var.set(previous_config["text"])
            self.hotkey_status_var.set(f"已恢复: {previous_config['text']}")
        else:
            self.current_hotkey_config = None
            self.hotkey_status_var.set("未注册")

        if show_error:
            messagebox.showerror("快捷键错误", "无法注册快捷键，请检查权限设置。")
        return False

    def start_hotkey_listener(self, hotkey_config):
        try:
            # 构建pynput格式的热键字符串
            # pynput要求使用<ctrl>、<alt>、<shift>、<cmd>格式
            hotkey_parts = hotkey_config["text"].split('+')
            pynput_hotkey = ''
            
            for part in hotkey_parts:
                part_lower = part.lower()
                if part_lower == 'ctrl':
                    pynput_hotkey += '<ctrl>+'
                elif part_lower == 'option' or part_lower == 'alt':
                    pynput_hotkey += '<alt>+'
                elif part_lower == 'shift':
                    pynput_hotkey += '<shift>+'
                elif part_lower == 'cmd':
                    pynput_hotkey += '<cmd>+'
                else:
                    pynput_hotkey += part
            
            # 构建热键字典
            hotkey_dict = {
                pynput_hotkey: self.start_from_hotkey
            }
            
            self.hotkey_listener = keyboard.GlobalHotKeys(hotkey_dict)
            self.hotkey_listener.start()
            return True
        except Exception as e:
            print(f"热键注册失败: {e}")
            return False

    def stop_hotkey_listener(self):
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except:
                pass
            self.hotkey_listener = None

    def start_from_hotkey(self):
        if self.simulation_active:
            return

        release_keys = ()
        if self.current_hotkey_config:
            release_keys = self.current_hotkey_config["release_keys"]
        self.simulate_input(skip_start_delay=True, release_keys=release_keys)

    def release_hotkey_keys(self, keyboard_controller, release_keys):
        for key in reversed(release_keys):
            keyboard_controller.release_key(key)

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
        
        # 实例化 macOS 键盘控制器
        keyboard_controller = MacOSKeyboardController()

        start_delay = 0 if skip_start_delay else self.delay_var.get()
        char_delay = self.interval_var.get()
        
        total_chars = repetitions * len(text_content)
        self.progress['maximum'] = total_chars
        self.progress['value'] = 0

        newline_mode = self.newline_mode_var.get()

        def do_newline():
            if newline_mode == "普通使用Enter换行":
                keyboard_controller.type_key(keyboard_controller.VK_RETURN)

            elif newline_mode == "使用Shift+Enter换行":
                with keyboard_controller.pressed(keyboard_controller.VK_SHIFT):
                    keyboard_controller.type_key(keyboard_controller.VK_RETURN)

            elif newline_mode == "换行后10次Shift+Tab":
                keyboard_controller.type_key(keyboard_controller.VK_RETURN)
                time.sleep(char_delay)
                for _ in range(10):
                    if self.stop_event.is_set(): break
                    with keyboard_controller.pressed(keyboard_controller.VK_SHIFT):
                        keyboard_controller.type_key(keyboard_controller.VK_TAB)
                    time.sleep(char_delay)

            elif newline_mode == "换行后2次Home回到行首":
                keyboard_controller.type_key(keyboard_controller.VK_RETURN)
                time.sleep(char_delay)
                for _ in range(2):
                    if self.stop_event.is_set(): break
                    keyboard_controller.type_key(keyboard_controller.VK_HOME)
                    time.sleep(char_delay)

        def simulate_input_thread():
            try:
                if not self.wait_with_stop(start_delay):
                    return

                if release_keys:
                    self.release_hotkey_keys(keyboard_controller, release_keys)

                for _ in range(repetitions):
                    if self.stop_event.is_set(): break
                    for char in text_content:
                        if self.stop_event.is_set(): break
                        
                        if char == "\n":
                            do_newline()
                        else:
                            keyboard_controller.type_char(char, char_delay)

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
    window.title('模拟键盘输入 (macOS版)')
    window.geometry('700x600')
    window.minsize(700, 600)

    app = KeyboardSimulator(window)
    window.mainloop()
