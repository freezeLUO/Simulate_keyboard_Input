from tkinter import *
from tkinter import scrolledtext, messagebox, filedialog
from tkinter import ttk  # 导入ttk用于更现代的控件
from pynput.keyboard import Controller
import time
import threading


class KeyboardSimulator:
    def __init__(self, window):
        self.window = window  # 保存对主窗口的引用
        self.window.configure(bg="#f0f0f0")  # 设置背景颜色
        # 默认不置顶
        self.window.attributes("-topmost", False)

        # 主框架
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

        # 延迟设置
        delay_frame = Frame(params_frame, bg="#f0f0f0")
        delay_frame.pack(fill="x", pady=5)

        ttk.Label(delay_frame, text="开始输入的延迟 (秒):", width=25, anchor='w', background="#f0f0f0").pack(side=LEFT, padx=(0, 5))

        self.delay_var = DoubleVar(value=2)
        self.scale_delay = ttk.Scale(
            delay_frame, from_=0, to=20, orient=HORIZONTAL, variable=self.delay_var, command=self.update_delay_label)
        self.scale_delay.pack(side=LEFT, fill="x", expand=True)

        self.delay_label = ttk.Label(delay_frame, text=f"{self.delay_var.get():.2f} 秒", width=10, anchor='w',
                                     background="#f0f0f0")
        self.delay_label.pack(side=LEFT, padx=(5, 0))

        # 间隔设置
        interval_frame = Frame(params_frame, bg="#f0f0f0")
        interval_frame.pack(fill="x", pady=5)

        ttk.Label(interval_frame, text="输入字符的间隔 (秒):", width=25, anchor='w', background="#f0f0f0").pack(side=LEFT,
                                                                                                       padx=(0, 5))

        self.interval_var = DoubleVar(value=0.05)
        self.scale_interval = ttk.Scale(
            interval_frame, from_=0.01, to=1, orient=HORIZONTAL, variable=self.interval_var,
            command=self.update_interval_label)
        self.scale_interval.pack(side=LEFT, fill="x", expand=True)

        self.interval_label = ttk.Label(interval_frame, text=f"{self.interval_var.get():.2f} 秒", width=10, anchor='w',
                                        background="#f0f0f0")
        self.interval_label.pack(side=LEFT, padx=(5, 0))

        # 重复次数设置
        repetition_frame = Frame(params_frame, bg="#f0f0f0")
        repetition_frame.pack(fill="x", pady=5)

        ttk.Label(repetition_frame, text="重复次数:", width=25, anchor='w', background="#f0f0f0").pack(side=LEFT,
                                                                                                 padx=(0, 5))
        self.repetition_entry = ttk.Entry(repetition_frame, width=10)
        self.repetition_entry.pack(side=LEFT, padx=(0, 5))
        self.repetition_entry.insert(0, "1")  # 默认值

        # ---------------- 控制按钮区域 ----------------
        controls_frame = Frame(main_frame, bg="#f0f0f0")
        controls_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        # 窗口置顶勾选框
        self.topmost_var = BooleanVar(value=False)
        self.topmost_check = ttk.Checkbutton(
            controls_frame, text='窗口始终置顶', variable=self.topmost_var,
            command=self.toggle_topmost, style='TCheckbutton')
        self.topmost_check.pack(side=LEFT, padx=5)

        self.clear_text_var = BooleanVar()
        self.clear_text_checkbutton = ttk.Checkbutton(
            controls_frame, text='执行后清除文本框', variable=self.clear_text_var, style='TCheckbutton')
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

        self.record_text = scrolledtext.ScrolledText(records_frame, wrap=WORD, width=60, height=10, state=DISABLED,
                                                    font=("Helvetica", 12))
        self.record_text.pack(expand=True, fill=BOTH, padx=5, pady=5)

        # ---------------- 进度条区域 ----------------
        progress_frame = Frame(main_frame, bg="#f0f0f0")
        progress_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)

        self.progress = ttk.Progressbar(progress_frame, orient=HORIZONTAL, length=500, mode='determinate')
        self.progress.pack(fill="x", expand=True, padx=5, pady=5)

        # 设置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)  # 输出记录区域可扩展
        records_frame.columnconfigure(0, weight=1)
        records_frame.rowconfigure(0, weight=1)

        # 初始化记录列表
        self.records = []
        self.stop_event = threading.Event()  # 停止事件
        self.input_thread = None  # 输入线程

        # 设置样式
        self.set_styles()

    def set_styles(self):
        style = ttk.Style()
        style.theme_use('clam')  # 使用'clam'主题，其他主题如 'default', 'classic', 'alt'

        # 按钮样式
        style.configure('TButton', font=('Microsoft YaHei', 10))
        style.configure('TCheckbutton', font=('Microsoft YaHei', 10))

        # 标签样式
        style.configure('TLabelframe.Label', font=('Microsoft YaHei', 12, 'bold'))

    def update_delay_label(self, event=None):
        self.delay_label.config(text=f"{self.delay_var.get():.2f} 秒")

    def update_interval_label(self, event=None):
        self.interval_label.config(text=f"{self.interval_var.get():.2f} 秒")

    def toggle_topmost(self):
        """切换窗口始终置顶属性"""
        self.window.attributes("-topmost", self.topmost_var.get())

    def simulate_input(self):
        # 输入验证
        try:
            repetitions = int(self.repetition_entry.get())
            if repetitions < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("输入错误", "请提供一个有效的正整数作为重复次数。")
            return

        self.stop_event.clear()  # 清除停止事件
        self.button_start.config(state=DISABLED)  # 禁用开始按钮
        self.button_stop.config(state=NORMAL)  # 启用停止按钮

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

        def simulate_input_thread():
            try:
                time.sleep(start_delay)
                for rep in range(repetitions):
                    if self.stop_event.is_set():
                        break
                    for char in text_content:
                        if self.stop_event.is_set():
                            break
                        keyboard.type(char)
                        self.window.after(0, self.progress.step, 1)
                        time.sleep(char_delay)
                    # 完成一次完整输入后记录
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    self.records.append(f"[{timestamp}] {text_content}")
                    self.window.after(0, self.update_record_text, f"[{timestamp}] {text_content}")
            finally:
                if self.clear_text_var.get():
                    self.window.after(0, self.text.delete, '1.0', 'end')
                self.window.after(0, self.finish_simulation)

        self.input_thread = threading.Thread(target=simulate_input_thread, daemon=True)
        self.input_thread.start()

    def finish_simulation(self):
        self.button_start.config(state=NORMAL)  # 启用开始按钮
        self.button_stop.config(state=DISABLED)  # 禁用停止按钮
        self.progress['value'] = 0  # 重置进度条
        # messagebox.showinfo("完成", "模拟输入已完成。")

    def stop_simulation(self):
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
        if not self.records:
            messagebox.showwarning("无记录", "没有记录可保存。")
            return
        file_path = filedialog.asksaveasfilename(defaultextension='.txt',
                                                 filetypes=[('Text files', '*.txt')],
                                                 title='保存记录')
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
    window.minsize(700, 600)  # 设置最小窗口尺寸

    app = KeyboardSimulator(window)
    window.mainloop()
