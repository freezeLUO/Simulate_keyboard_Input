# 导入tkinter模块
import tkinter as tk
import pynput
import time
# 创建一个窗口
window = tk.Tk()
window.title('模拟输入GUI')
window.geometry('450x300')

text = tk.Text(window, wrap=tk.WORD, width=20, height=5)
text.pack(expand=True, fill=tk.BOTH)
# 创建一个函数来实现模拟输入的功能
def simulate_input():
    # 获取文本框中的内容
    text_content = text.get('1.0', 'end')
    keyboard = pynput.keyboard.Controller()

    delay_3 = scale_3.get()
    # 延迟用户选择的时间
    time.sleep(delay_3)

    delay_005 = scale_005.get()
    # 模拟键盘输入字符串，每个字符之间延迟用户选择的时间
    for char in text_content:
        keyboard.type(char)
        time.sleep(delay_005)  

button = tk.Button(window, text='确认', command=simulate_input)
button.pack()
# 创建一个Scale组件，用于选择开始输入的延迟的时间
scale_3 = tk.Scale(window, from_=0, to=20, orient=tk.HORIZONTAL, label='开始输入的延迟', length=200)
scale_3.pack()
# 创建一个Scale组件，用于选择输入字符的间隔延迟秒的时间
scale_005 = tk.Scale(window, from_=0.01, to=1, orient=tk.HORIZONTAL, label='输入字符的间隔', resolution=0.01, length=200)
scale_005.pack()
# 运行窗口
window.mainloop()



