import tkinter as tk
from pynput.keyboard import Controller
import time
import threading
from tkinter import messagebox

class KeyboardSimulator:
    def __init__(self, window):
        self.window = window
        self.text = tk.Text(window, wrap=tk.WORD, width=20, height=5)
        self.text.pack(expand=True, fill=tk.BOTH)

        self.scale_3 = tk.Scale(window, from_=0, to=20, orient=tk.HORIZONTAL, label='开始输入的延迟', length=200)
        self.scale_3.pack()
        self.scale_3.set(2)
        self.scale_005 = tk.Scale(window, from_=0.01, to=1, orient=tk.HORIZONTAL, label='输入字符的间隔', resolution=0.01, length=200)
        self.scale_005.pack()

        self.repetition_label = tk.Label(window, text='重复次数:')
        self.repetition_label.pack()
        self.repetition_entry = tk.Entry(window)
        self.repetition_entry.pack()

        self.button = tk.Button(window, text='开始输入', command=self.simulate_input)
        self.button.pack()

        self.clear_text_var = tk.BooleanVar()
        self.clear_text_checkbutton = tk.Checkbutton(window, text='执行后清除文本框', variable=self.clear_text_var)
        self.clear_text_checkbutton.pack()

    def simulate_input(self):
        text_content = self.text.get('1.0', 'end-1c')
        keyboard = Controller()

        start_delay = self.scale_3.get()
        char_delay = self.scale_005.get()
        repetitions = int(self.repetition_entry.get() or 1)

        def simulate_input_thread():
            time.sleep(start_delay)
            for _ in range(repetitions):
                for char in text_content:
                    keyboard.type(char)
                    time.sleep(char_delay)
            if self.clear_text_var.get():
                self.text.delete('1.0', 'end')

        thread = threading.Thread(target=simulate_input_thread)
        thread.start()

if __name__ == "__main__":
    window = tk.Tk()
    window.title('模拟键盘输入')
    window.geometry('450x300')

    app = KeyboardSimulator(window)
    window.mainloop()
