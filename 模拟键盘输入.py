# 导入tkinter模块
import tkinter as tk
import pynput
import time

# 创建一个窗口
window = tk.Tk()
window.title('模拟输入GUI(延迟3s后开始输入)')
window.geometry('450x300')

# 创建一个文本框
text = tk.Text(window, wrap=tk.WORD, width=20, height=5)
text.pack(expand=True, fill=tk.BOTH)

# 创建一个函数来实现模拟输入的功能
def simulate_input():
    # 获取文本框中的内容
    text_content = text.get('1.0', 'end')

    keyboard = pynput.keyboard.Controller()

    time.sleep(3)

    #keyboard.type(text_content)
    for char in text_content:
        keyboard.type(char)
        time.sleep(0.05)  


button = tk.Button(window, text='确认', command=simulate_input)
button.pack()
window.mainloop()


