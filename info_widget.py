import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from file_manager import FileData, IssueType, Issue

@dataclass
class GUIError:
    pass

class InfoWidget(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.text = tk.Text(self, wrap='none', state='disabled', font="Arial 11")
        self.info_count = 0
        self.issue_list:list[Issue] = []

        self.text.tag_configure('spacer', font='Arial 3')
        self.text.tag_configure('spacer2', font='Arial 2')
        self.text.tag_configure('even', background="#EEEEEE", foreground="black")
        self.text.tag_configure('odd', background="#DDDDDD", foreground="black")
        self.text.tag_configure('error', background='#F7B0B0')
        self.text.tag_configure('warning', background='#F7CCB0')
        self.text.tag_configure('issue_message', font="Arial 11 bold")
        
        self.text.insert("1.0", "Info\n", ('info'))
        self.text.insert("1.0", "Warning\n", ('warning'))
        self.text.insert("1.0", "Error\n", ('error'))
        self.text['state'] = 'disabled'

        self.ys = ttk.Scrollbar(self, orient='vertical', command=self.text.yview)
        self.text['yscrollcommand'] = self.ys.set

        self.xs = ttk.Scrollbar(self, orient='horizontal', command=self.text.xview)
        self.text['xscrollcommand'] = self.xs.set

        self.text.grid(column=0, row=0, sticky='nsew')
        self.ys.grid(column=1, row=0, sticky='ns')
        self.xs.grid(column=0, row=1, sticky='ew')

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def render(self):
        self.text['state'] = 'normal'
        self.text.delete('1.0', 'end')
        bg_tag = 'even'
        for i in self.issue_list:
            if bg_tag == 'even':
                bg_tag = 'odd'
            elif bg_tag == 'odd':
                bg_tag = 'even'

            match i.issue_type:
                case IssueType.SUBPROGRAM_1_ERR:
                    self.text.insert('end', '\n', ('error', 'spacer2'))
                    self.text.insert('end'," Error: Subprogram Missing\n", ('error', 'issue_message', bg_tag))
                    self.text.insert('end',' ' + i.message + '\n', ('error', bg_tag))
                    self.text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.INVALID_NAME_ERR:
                    self.text.insert('end', '\n', ('error', 'spacer2'))
                    self.text.insert('end'," Error: Invalid Name\n", ('error', 'issue_message', bg_tag))
                    self.text.insert('end',' ' + i.message + '\n', ('error', bg_tag))
                    self.text.insert('end', '\n', ('error', 'spacer2'))
            self.text.insert('end', '\n', ('spacer'))
        self.text['state'] = 'disabled'
    
    def addError():
        pass


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("500x300")
    root.minsize(500, 300)
    f = tk.Frame(root)

    # fd = FileData.from_path(r'\\192.168.1.100\Trubox\####ERP_RM####\Y2024\M09\D13\1. CAM\3. NC files\Isaac\4001.prg')
    infoWidget = InfoWidget(root)

    btn_frame = tk.Frame(root, padx=5, pady=5)
    toggle = tk.Checkbutton(btn_frame, text="Auto Gather")
    btn = tk.Button(btn_frame, text="Gather ALL NC", padx=20, pady=20)
    btn2 = tk.Button(btn_frame, text="Gather ALL ASC", padx=20, pady=20)

    toggle.pack(side=tk.TOP)
    btn.pack(fill=tk.X, side=tk.TOP)
    btn2.pack(fill=tk.X, side=tk.TOP)

    btn_frame.grid(row=0, column=0, sticky='nsew')
    infoWidget.grid(row=0, column=1, sticky='nsew')

    root.grid_columnconfigure(0, weight=0)
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)

    root.mainloop()