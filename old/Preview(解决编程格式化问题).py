from tkinter import *
from tkinter import scrolledtext, messagebox, filedialog
from tkinter import ttk
from pynput.keyboard import Controller, Key
import time
import threading


class KeyboardSimulator:
    def __init__(self, window):
        self.window = window
        self.window.configure(bg="#f0f0f0")
        # 默认不置顶
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
        self.repetition_entry.insert(0, "1")  # 默认值

        # ----- 换行方式下拉框 -----
        newline_mode_frame = Frame(params_frame, bg="#f0f0f0")
        newline_mode_frame.pack(fill="x", pady=5)

        ttk.Label(newline_mode_frame, text="换行方式:", width=25, anchor='w', background="#f0f0f0").pack(
            side=LEFT, padx=(0, 5)
        )

        self.newline_mode_var = StringVar(value="普通使用Enter换行")  # 默认选项
        self.newline_options = [
            "普通使用Enter换行",       # 1
            "使用Shift+Enter换行",    # 2
            "换行后10次Shift+Tab",   # 3
            "换行后2次Home回到行首"   # 4
        ]

        self.newline_mode_combobox = ttk.Combobox(
            newline_mode_frame,
            textvariable=self.newline_mode_var,
            values=self.newline_options,
            state="readonly",       # 只读
            width=20
        )
        self.newline_mode_combobox.current(0)  # 默认选中第 0 项
        self.newline_mode_combobox.pack(side=LEFT, padx=(0, 5))

        # ---------------- 控制按钮区域 ----------------
        controls_frame = Frame(main_frame, bg="#f0f0f0")
        controls_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        # 窗口始终置顶
        self.topmost_var = BooleanVar(value=False)
        self.topmost_check = ttk.Checkbutton(
            controls_frame, text='窗口始终置顶', variable=self.topmost_var,
            command=self.toggle_topmost, style='TCheckbutton'
        )
        self.topmost_check.pack(side=LEFT, padx=5)

        # 执行后清空文本
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
        records_frame.columnconfigure(0, weight=1)
        records_frame.rowconfigure(0, weight=1)

        self.records = []
        self.stop_event = threading.Event()
        self.input_thread = None

        self.set_styles()

    def set_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Microsoft YaHei', 10))
        style.configure('TCheckbutton', font=('Microsoft YaHei', 10))
        style.configure('TLabelframe.Label', font=('Microsoft YaHei', 12, 'bold'))

    def update_delay_label(self, event=None):
        self.delay_label.config(text=f"{self.delay_var.get():.2f} 秒")

    def update_interval_label(self, event=None):
        self.interval_label.config(text=f"{self.interval_var.get():.2f} 秒")

    def toggle_topmost(self):
        self.window.attributes("-topmost", self.topmost_var.get())

    def simulate_input(self):
        """开始模拟输入"""
        try:
            repetitions = int(self.repetition_entry.get())
            if repetitions < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("输入错误", "请提供一个有效的正整数作为重复次数。")
            return

        self.stop_event.clear()
        self.button_start.config(state=DISABLED)
        self.button_stop.config(state=NORMAL)

        text_content = self.text.get('1.0', 'end-1c')
        if not text_content.strip():
            messagebox.showwarning("输入警告", "请输入要模拟的内容。")
            self.button_start.config(state=NORMAL)
            self.button_stop.config(state=DISABLED)
            return

        keyboard = Controller()

        start_delay = self.delay_var.get()
        char_delay = self.interval_var.get()

        total_chars = repetitions * len(text_content)
        self.progress['maximum'] = total_chars
        self.progress['value'] = 0

        # 读取当前选择的换行模式
        newline_mode = self.newline_mode_var.get()

        def do_newline():
            """
            根据用户在下拉框选的方案，执行不同的"换行"方式。
            """
            if newline_mode == "普通使用Enter换行":
                # 1. 普通 Enter
                keyboard.press(Key.enter)
                keyboard.release(Key.enter)

            elif newline_mode == "使用Shift+Enter换行":
                # 2. Shift + Enter
                with keyboard.pressed(Key.shift):
                    keyboard.press(Key.enter)
                    keyboard.release(Key.enter)

            elif newline_mode == "换行后10次Shift+Tab":
                # 3. Enter + 10 次 Shift+Tab
                keyboard.press(Key.enter)
                keyboard.release(Key.enter)
                # 可以在 Enter 与 Shift+Tab 间也做一次 sleep，以免太快
                time.sleep(char_delay)
                for _ in range(10):
                    with keyboard.pressed(Key.shift):
                        keyboard.press(Key.tab)
                        keyboard.release(Key.tab)
                    time.sleep(char_delay)

            elif newline_mode == "换行后2次Home回到行首":
                # 4. Enter + 2 次 Home
                keyboard.press(Key.enter)
                keyboard.release(Key.enter)
                time.sleep(char_delay)
                for _ in range(2):
                    keyboard.press(Key.home)
                    keyboard.release(Key.home)
                    time.sleep(char_delay)

            else:
                # 如果扩展了更多模式，可以在此继续写 else if
                pass

        def simulate_input_thread():
            try:
                # 起始延时
                time.sleep(start_delay)
                # 重复次数
                for _ in range(repetitions):
                    if self.stop_event.is_set():
                        break
                    for char in text_content:
                        if self.stop_event.is_set():
                            break
                        # 如果是换行符，则根据下拉框选项执行相应的“换行”逻辑
                        if char == "\n":
                            do_newline()
                            # 换行逻辑执行完后不再调用 keyboard.type("\n")
                            # 因为 do_newline() 已经按下了 Enter 或 Shift+Enter 等
                        else:
                            # 正常字符
                            keyboard.type(char)

                        # 更新进度条
                        self.window.after(0, self.progress.step, 1)

                        # 每按一次键，都等待一下
                        time.sleep(char_delay)

                    # 一次完整输入后，记录
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    record_line = f"[{timestamp}] {text_content}"
                    self.records.append(record_line)
                    self.window.after(0, self.update_record_text, record_line)

            finally:
                # 如果勾选了“执行后清除文本框”，则在主线程里清空
                if self.clear_text_var.get():
                    self.window.after(0, self.text.delete, '1.0', 'end')
                # 线程结束时在主线程中收尾
                self.window.after(0, self.finish_simulation)

        self.input_thread = threading.Thread(target=simulate_input_thread, daemon=True)
        self.input_thread.start()

    def finish_simulation(self):
        """线程结束时的收尾操作"""
        self.button_start.config(state=NORMAL)
        self.button_stop.config(state=DISABLED)
        self.progress['value'] = 0

    def stop_simulation(self):
        """手动停止"""
        self.stop_event.set()
        self.button_stop.config(state=DISABLED)
        self.button_start.config(state=NORMAL)
        messagebox.showinfo("停止", "模拟输入已停止。")

    def update_record_text(self, new_entry):
        self.record_text.config(state=NORMAL)
        self.record_text.insert('end', new_entry + '\n')
        self.record_text.see('end')
        self.record_text.config(state=DISABLED)

    def save_records_to_file(self):
        """保存记录到文件"""
        if not self.records:
            messagebox.showwarning("无记录", "没有记录可保存。")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text files', '*.txt')],
            title='保存记录'
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
    window.title('模拟键盘输入')
    window.geometry('700x600')
    window.minsize(700, 600)

    app = KeyboardSimulator(window)
    window.mainloop()
