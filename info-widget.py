import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass

import enum

class InfoType(enum.Enum):
    INFO=1
    WARNING=2
    ERROR=3

class IssueType(enum.Enum):
    SUBPROGRAM_ERR=1
    INVALID_NAME_ERR=2
    DUPLICATE_PRG=3

@dataclass
class Issue:
    issue_type:IssueType
    id:str
    associate:str
    folder:str
    message:str

@dataclass
class Info:
    info_type:InfoType
    header:str  
    message:str


class InfoWidget(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.text = tk.Text(self, wrap='word', state='disabled', font="Arial 16")
        self.info_count = 0
        self.issue_list:list[Issue] = []

        self.text.tag_configure('spacer', font='Arial 3')
        self.text.tag_configure('spacer2', font='Arial 2')
        self.text.tag_configure('even', background="#EEEEEE", foreground="black")
        self.text.tag_configure('odd', background="#DDDDDD", foreground="black")
        self.text.tag_configure('error', background='#F7B0B0')
        self.text.tag_configure('warning', background='#F7CCB0')
        # self.text.tag_configure('info', background=('grey'))
        # self.text.tag_configure('error', background='red', foreground='white')
        
        self.text.insert("1.0", "Info\n", ('info'))
        self.text.insert("1.0", "Warning\n", ('warning'))
        self.text.insert("1.0", "Error\n", ('error'))
        self.text['state'] = 'disabled'

        self.ys = ttk.Scrollbar(self, orient='vertical', command=self.text.yview)
        self.text['yscrollcommand'] = self.ys.set

        self.text.grid(column=0, row=0, sticky='nsew')
        self.ys.grid(column=1, row=0, sticky='ns')

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

            header = f' {i.id} {i.associate} {i.folder}'
            message = f' {i.message} '

            match i.issue_type:
                case IssueType.SUBPROGRAM_ERR:
                    self.text.insert('end', '\n', ('error', 'spacer2'))
                    self.text.insert('end',header + '\n', ('error', bg_tag))
                    self.text.insert('end',message + '\n', ('error', bg_tag))
                    self.text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.INVALID_NAME_ERR:
                    self.text.insert('end', '\n', ('error', 'spacer2'))
                    self.text.insert('end',header + '\n', ('error', bg_tag))
                    self.text.insert('end',message + '\n', ('error', bg_tag))
                    self.text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.DUPLICATE_PRG:
                    self.text.insert('end', '\n', ('warning', 'spacer2'))
                    self.text.insert('end',header + '\n', ('warning', bg_tag))
                    self.text.insert('end',message + '\n', ('warning', bg_tag))
                    self.text.insert('end', '\n', ('warning', 'spacer2'))
            self.text.insert('end', '\n', ('spacer'))
        self.text['state'] = 'disabled'
    
    def addIssue(self, issue):
        self.issue_list.append(issue)
        self.render()


if __name__ == "__main__":
    i = Issue(IssueType.SUBPROGRAM_ERR, "1234", "Isaac", "1", "Mising sub program $2")
    i2 = Issue(IssueType.INVALID_NAME_ERR, "4001", "Ryan", "4", "Invalid PRG name")
    i3 = Issue(IssueType.INVALID_NAME_ERR, "0", "Eduardo", "2", "Invalid PRG name")
    i3 = Issue(IssueType.DUPLICATE_PRG, "3333", "Ryan", "4", "3333 also in Isaac's Folder 2")

    root = tk.Tk()
    root.geometry("500x300")
    root.minsize(500, 300)
    f = tk.Frame(root)

    infoWidget = InfoWidget(root)
    infoWidget.addIssue(i)
    infoWidget.addIssue(i2)
    infoWidget.addIssue(i3)

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