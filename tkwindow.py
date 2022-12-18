import os
import contextlib
import tkinter as tk
import tkinter.ttk as ttk
from pathlib import Path
from tkinter import filedialog

from db_manage import get_names


COLORS = [
    '#000000', '#696969', '#808080', '#a9a9a9', '#c0c0c0', '#d3d3d3', '#dcdcdc', '#f5f5f5', '#ffffff', '#fffafa',
    '#f8f8ff', '#fffaf0', '#faf0e6', '#faebd7', '#ffefd5', '#ffebcd', '#ffe4c4', '#ffe4b5', '#ffdead', '#ffdab9',
    '#ffe4e1', '#fff0f5', '#fff5ee', '#fdf5e6', '#fffff0', '#f0fff0', '#f5fffa', '#f0ffff', '#f0f8ff', '#e6e6fa',
    '#b0c4de', '#778899', '#708090', '#4682b4', '#4169e1', '#191970', '#000080', '#00008b', '#0000cd', '#0000ff',
    '#1e90ff', '#6495ed', '#00bfff', '#87cefa', '#87ceeb', '#add8e6', '#b0e0e6', '#afeeee', '#e0ffff', '#00ffff',
    '#00ffff', '#40e0d0', '#48d1cc', '#00ced1', '#20b2aa', '#5f9ea0', '#008b8b', '#008080', '#2f4f4f', '#006400',
    '#008000', '#228b22', '#2e8b57', '#3cb371', '#66cdaa', '#8fbc8f', '#7fffd4', '#98fb98', '#90ee90', '#00ff7f',
    '#00fa9a', '#7cfc00', '#7fff00', '#adff2f', '#00ff00', '#32cd32', '#9acd32', '#556b2f', '#6b8e23', '#808000',
    '#bdb76b', '#eee8aa', '#fff8dc', '#f5f5dc', '#ffffe0', '#fafad2', '#fffacd', '#f5deb3', '#deb887', '#d2b48c',
    '#f0e68c', '#ffff00', '#ffd700', '#ffa500', '#f4a460', '#ff8c00', '#daa520', '#cd853f', '#b8860b', '#d2691e',
    '#a0522d', '#8b4513', '#800000', '#8b0000', '#a52a2a', '#b22222', '#cd5c5c', '#bc8f8f', '#e9967a', '#f08080',
    '#fa8072', '#ffa07a', '#ff7f50', '#ff6347', '#ff4500', '#ff0000', '#dc143c', '#c71585', '#ff1493', '#ff69b4',
    '#db7093', '#ffc0cb', '#ffb6c1', '#d8bfd8', '#ff00ff', '#ff00ff', '#ee82ee', '#dda0dd', '#da70d6', '#ba55d3',
    '#9932cc', '#9400d3', '#8b008b', '#800080', '#4b0082', '#483d8b', '#8a2be2', '#9370db', '#6a5acd', '#7b68ee'
]


@contextlib.contextmanager
def change_dir(path):
    prev_dir = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_dir)


class WindowTk(ttk.Frame):

    def __init__(self, master, panda_app):
        super().__init__(master)
        self.pack(fill=tk.Y, side=tk.LEFT, pady=10)
        self.panda_app = panda_app

        self.make_gui()
        self.make_menubar()

    def selected_color(self):
        color = self.selected_color_label.cget('background')
        return str(color)

    def make_menubar(self):
        menubar = tk.Menu(self)
        menu_file = tk.Menu(menubar, tearoff=False)
        menu_file.add_command(label='Save As', command=self.save_file, accelerator='Ctrl+S')
        menu_file.add_separator()
        menu_file.add_command(label='close', command=self.close)
        menu_file.bind_all('<Control-s>', self.save_file)

        menubar.add_cascade(label="File", menu=menu_file)
        self.master.config(menu=menubar)

    def make_gui(self):
        self.make_selected_color_display()
        self.make_basic_color_panel()
        self.custom_labels = [label for label in self.make_custom_color_panel()]
        self.custom_idx = 0
        self.make_gradation_picker()
        self.make_button()
        self.make_coloring_pic_controllers()

    def make_selected_color_display(self):
        frame = ttk.Frame(self)
        frame.pack(side=tk.TOP, padx=10, pady=10)
        label = ttk.Label(frame, text='Selected Color : ')
        label.pack(side=tk.LEFT)
        self.selected_color_label = ttk.Label(frame, width=22, relief=tk.SUNKEN)
        self.selected_color_label.pack(side=tk.LEFT)

    def make_basic_color_panel(self):
        frame = ttk.Frame(self)
        frame.pack(side=tk.TOP, padx=10, pady=10)

        for i, color in enumerate(COLORS):
            r = i // 14
            c = i % 14
            label = ttk.Label(frame, width=2, relief=tk.SUNKEN, background=color)
            label.grid(column=c, row=r, padx=0.3, pady=0.3)
            label.bind('<Button-1>', self.show_selected_color)

    def make_custom_color_panel(self):
        frame = ttk.Frame(self)
        frame.pack(side=tk.TOP, padx=10, pady=10)

        for r in range(2):
            for c in range(14):
                label = ttk.Label(frame, width=2, relief=tk.SUNKEN)
                label.grid(column=c, row=r, padx=0.3, pady=0.3)
                label.bind('<Button-1>', self.show_selected_color)
                yield label

    def make_gradation_picker(self):
        frame = ttk.Frame(self)
        frame.pack(side=tk.TOP, padx=10, pady=10)
        self.r_picker = GradationPicker('R', self.make_color, frame)
        self.g_picker = GradationPicker('G', self.make_color, frame)
        self.b_picker = GradationPicker('B', self.make_color, frame)

    def make_button(self):
        frame = ttk.Frame(self)
        frame.pack(side=tk.TOP, padx=10, pady=10)

        self.created_color_label = ttk.Label(
            frame, width=10, relief=tk.SUNKEN, background='#000000')
        self.created_color_label.pack(side=tk.LEFT)
        btn = tk.Button(
            frame, text='Add Custom Colors', width=20, command=self.add_custom_color)
        btn.pack(side=tk.LEFT, padx=(10, 1))

    def make_coloring_pic_controllers(self):
        frame = ttk.Frame(self)
        frame.pack(side=tk.TOP, padx=10, pady=10)

        self.var_radio = tk.IntVar(value=1)
        label_lines = ttk.Label(frame, text='Outline : ')
        label_lines.grid(column=0, row=0, pady=5)

        for i, (text, val) in enumerate(zip(['Show', 'Not Show'], [1, 0]), start=1):
            radio_btn = ttk.Radiobutton(
                frame, text=text, value=val, variable=self.var_radio, command=self.toggle_radio)
            radio_btn.grid(column=i, row=0, pady=5)

        item_list = get_names()

        self.combobox = ttk.Combobox(
            master=frame,
            values=item_list,
            justify='left',
            state='readonly',
            height=10,
            width=35
        )
        self.combobox.grid(column=0, row=1, columnspan=3, pady=5)
        self.combobox.bind('<<ComboboxSelected>>', self.show_coloring_pic)
        self.combobox.set(item_list[0])
        btn = tk.Button(frame, text='Save', width=32, command=self.save_file)
        btn.grid(column=0, row=2, columnspan=3, pady=5)

    def show_selected_color(self, event):
        if color := event.widget.cget('background'):
            self.selected_color_label.configure(background=color)

    def add_custom_color(self):
        color = self.created_color_label.cget('background')
        if self.custom_idx == len(self.custom_labels):
            self.custom_idx = 0
        label = self.custom_labels[self.custom_idx]
        label.configure(background=color)
        self.custom_idx += 1

    def make_color(self, value, text):
        color = str(self.created_color_label.cget('background'))
        value = hex(value).replace('0x', '').zfill(2)

        if text == 'R':
            new_color = f'#{value}{color[3:]}'
        elif text == 'G':
            new_color = f'{color[:3]}{value}{color[5:]}'
        elif text == 'B':
            new_color = f'{color[:5]}{value}'

        self.created_color_label.configure(background=new_color)

    def save_file(self):
        initialfile = self.combobox.get().replace(' ', '')
        if filepath := filedialog.asksaveasfilename(
                title='Save as',
                filetypes=[('bam', '.bam')],
                initialdir='./',
                defaultextension='bam',
                initialfile=initialfile):
            filepath = Path(filepath)

            # Using WindowsPath causes an error.
            with change_dir(filepath.parent):
                self.panda_app.make_file(filepath)

    def show_coloring_pic(self, event=None):
        name = self.combobox.get()
        self.panda_app.show_coloring_pic(name)

    def toggle_radio(self, event=None):
        outline = self.var_radio.get()
        self.panda_app.toggle_debug(outline)

    def close(self, event=None):
        self.quit()


class GradationPicker(ttk.Frame):

    def __init__(self, text, func, master):
        super().__init__(master)
        self.pack(side=tk.TOP)
        self.make_picker(text)
        self.make_color = func
        self.text = text

    def make_picker(self, text):
        self.var = tk.StringVar(value=0, name=text)
        self.var.trace_add('write', self.change_scale)

        label = ttk.Label(self, text=text, font=('', '10', 'bold'))
        label.grid(row=1, column=0)
        self.entry = ttk.Entry(self, width=5, textvariable=self.var)
        self.entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        self.scale = ttk.Scale(self, from_=0, to=255, length=180, command=self.display_value)
        self.scale.grid(row=1, column=3)

    def display_value(self, value):
        value = int(float(value))
        self.var.set(value)
        self.entry.icursor(len(self.var.get()))
        self.make_color(value, self.text)

    def change_scale(self, *args):
        if val := self.var.get():
            if int(float(self.scale.get())) != int(val):
                self.scale.set(int(val))
