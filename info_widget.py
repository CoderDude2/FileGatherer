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
        new_text = tk.Text(self)

        new_text.tag_configure('spacer', font='Arial 3')
        new_text.tag_configure('spacer2', font='Arial 2')
        new_text.tag_configure('even', background="#EEEEEE", foreground="black")
        new_text.tag_configure('odd', background="#DDDDDD", foreground="black")
        new_text.tag_configure('error', background='#F7B0B0')
        new_text.tag_configure('warning', background='#F7CCB0')
        new_text.tag_configure('issue_message', font="Arial 11 bold")

        self.ys.configure(command=new_text.yview)
        self.xs.configure(command=new_text.xview)

        new_text['state'] = 'normal'
        bg_tag = 'even'
        for i in self.issue_list:
            if bg_tag == 'even':
                bg_tag = 'odd'
            elif bg_tag == 'odd':
                bg_tag = 'even'

            match i.issue_type:
                case IssueType.SUBPROGRAM_0_ERR:
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                    new_text.insert('end'," Error: Subprogram Missing\n", ('error', 'issue_message', bg_tag))
                    new_text.insert('end',' ' + i.message + '\n', ('error', bg_tag))
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.SUBPROGRAM_1_ERR:
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                    new_text.insert('end'," Error: Subprogram Missing\n", ('error', 'issue_message', bg_tag))
                    new_text.insert('end',' ' + i.message + '\n', ('error', bg_tag))
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.SUBPROGRAM_2_ERR:
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                    new_text.insert('end'," Error: Subprogram Missing\n", ('error', 'issue_message', bg_tag))
                    new_text.insert('end',' ' + i.message + '\n', ('error', bg_tag))
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.INVALID_NAME_ERR:
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                    new_text.insert('end'," Error: Invalid Name\n", ('error', 'issue_message', bg_tag))
                    new_text.insert('end',' ' + i.message + '\n', ('error', bg_tag))
                    new_text.insert('end', '\n', ('error', 'spacer2'))
            new_text.insert('end', '\n', ('spacer'))
        new_text['state'] = 'disabled'

        self.text.destroy()
        self.text = new_text
        new_text.grid(column=0, row=0, sticky='nsew')
        self.grid(row=0, column=1, sticky='nsew')
    
    def addErrors(self, fd:FileData):
        for issue in fd.issues:
            if issue not in self.issue_list:
                self.issue_list.append(issue)
        self.render()





if __name__ == "__main__":
    fd = FileData()
    def testFunc():
        fd = FileData.from_path(r'/Users/isaacboots/Documents/GitHub/FileGatherer/nc/Ashley/5 (10) TL DS/1723.prg')
        infoWidget.addErrors(fd)
    root = tk.Tk()
    root.geometry("500x300")
    root.minsize(500, 300)
    f = tk.Frame(root)

    
    infoWidget = InfoWidget(root)
    

    btn_frame = tk.Frame(root, padx=5, pady=5)
    testbtn = tk.Button(btn_frame,command=testFunc)
    toggle = tk.Checkbutton(btn_frame, text="Auto Gather")
    btn = tk.Button(btn_frame, text="Gather ALL NC", padx=20, pady=20, width=10)
    btn2 = tk.Button(btn_frame, text="Gather ALL ASC", padx=20, pady=20, width=10)

    testbtn.pack(side=tk.TOP)
    toggle.pack(side=tk.TOP)
    btn.pack(fill=tk.X, side=tk.TOP)
    btn2.pack(fill=tk.X, side=tk.TOP)

    btn_frame.grid(row=0, column=0, sticky='nsew')
    infoWidget.grid(row=0, column=1, sticky='nsew')

    root.grid_columnconfigure(0, weight=0)
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)
    root.mainloop()