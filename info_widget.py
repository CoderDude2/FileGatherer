import time
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from file_manager import FileManager, IssueType
import threading

@dataclass
class GUIError:
    file:str
    location:str
    issue_type:IssueType

    def __eq__(self, other):
        return self.file == other.file and self.location == other.location and self.issue_type == other.issue_type

class InfoWidget(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.text = tk.Text(self, wrap='none', state='normal', font="Arial 11")

        self.text.insert('end', "Processing...")

        self.info_count = 0
        self.issue_list:list[GUIError] = []

        self.text.tag_configure('spacer', font='Arial 3')
        self.text.tag_configure('spacer2', font='Arial 2')
        self.text.tag_configure('even', background="#EEEEEE", foreground="black", selectforeground="white", selectbackground="blue")
        self.text.tag_configure('odd', background="#DDDDDD", foreground="black", selectforeground="white", selectbackground="blue")
        self.text.tag_configure('error', background='#F7B0B0', selectforeground="white", selectbackground="blue")
        self.text.tag_configure('warning', background='#F7CCB0', selectforeground="white", selectbackground="blue")
        self.text.tag_configure('issue_message', font="Arial 11 bold", selectforeground="white", selectbackground="blue")
        
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
        new_text = tk.Text(self,wrap='none', font="Arial 11", state='disabled')

        new_text.tag_configure('spacer', font='Arial 3')
        new_text.tag_configure('spacer2', font='Arial 2')
        new_text.tag_configure('even', background="#EEEEEE", foreground="black", selectforeground="white", selectbackground="blue")
        new_text.tag_configure('odd', background="#DDDDDD", foreground="black", selectforeground="white", selectbackground="blue")
        new_text.tag_configure('error', background='#F7B0B0', selectforeground="white", selectbackground="blue")
        new_text.tag_configure('warning', background='#F7CCB0', selectforeground="white", selectbackground="blue")
        new_text.tag_configure('issue_message', font="Arial 11 bold", selectforeground="white", selectbackground="blue")

        self.ys.configure(command=new_text.yview)
        new_text['yscrollcommand'] = self.ys.set

        self.xs.configure(command=new_text.xview)
        new_text['xscrollcommand'] = self.xs.set

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
                    new_text.insert('end'," Error: $0 Subprogram Missing\n", ('error', 'issue_message', bg_tag))
                    new_text.insert('end', f' File: {i.file} \n', ('error', bg_tag))
                    new_text.insert('end', f' Location: {i.location} \n', ('error', bg_tag))
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.SUBPROGRAM_1_ERR:
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                    new_text.insert('end'," Error: $1 Subprogram Missing\n", ('error', 'issue_message', bg_tag))
                    new_text.insert('end', f' File: {i.file} \n', ('error', bg_tag))
                    new_text.insert('end', f' Location: {i.location} \n', ('error', bg_tag))
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.SUBPROGRAM_2_ERR:
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                    new_text.insert('end'," Error: $2 Subprogram Missing\n", ('error', 'issue_message', bg_tag))
                    new_text.insert('end', f' File: {i.file} \n', ('error', bg_tag))
                    new_text.insert('end', f' Location: {i.location} \n', ('error', bg_tag))
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.INVALID_NAME_ERR:
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                    new_text.insert('end'," Error: Invalid Name\n", ('error', 'issue_message', bg_tag))
                    new_text.insert('end', f' File: {i.file} \n', ('error', bg_tag))
                    new_text.insert('end', f' Location: {i.location} \n', ('error', bg_tag))
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.PART_LENGTH_ERR:
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                    new_text.insert('end'," Error: Part-Length does not equal Cut-off\n", ('error', 'issue_message', bg_tag))
                    new_text.insert('end', f' File: {i.file} \n', ('error', bg_tag))
                    new_text.insert('end', f' Location: {i.location} \n', ('error', bg_tag))
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.MISSING_UG_VALUES_ERR:
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                    new_text.insert('end'," Error: Missing one or more UG values\n", ('error', 'issue_message', bg_tag))
                    new_text.insert('end', f' File: {i.file} \n', ('error', bg_tag))
                    new_text.insert('end', f' Location: {i.location} \n', ('error', bg_tag))
                    new_text.insert('end', '\n', ('error', 'spacer2'))
                case IssueType.DUPLICATE_PRG_ERR:
                    new_text.insert('end', '\n', ('warning', 'spacer2'))
                    new_text.insert('end'," Warning: Duplicate PRG\n", ('warning', 'issue_message', bg_tag))
                    new_text.insert('end', f' File: {i.file} \n', ('warning', bg_tag))
                    new_text.insert('end', f' Location: {i.location} \n', ('warning', bg_tag))
                    new_text.insert('end', '\n', ('warning', 'spacer2'))
            new_text.insert('end', '\n', ('spacer'))
        new_text['state'] = 'disabled'

        self.text.destroy()
        self.text = new_text
        new_text.grid(column=0, row=0, sticky='nsew')
        self.grid(row=0, column=1, sticky='nsew')
    
    def updateErrors(self, fm:FileManager):
        self.issue_list = []
        for entry in fm.processed_files:
            if len(fm.processed_files[entry]['errors']) > 0:
                for error in fm.processed_files[entry]['errors']:
                    gui_error = GUIError(entry, fm.processed_files[entry]['location'], error)
                    if gui_error not in self.issue_list:
                        self.issue_list.append(gui_error)
            if len(fm.processed_files[entry]['duplicates']) > 0:
                for duplicate in fm.processed_files[entry]['duplicates']:
                    for error in duplicate['errors']:
                        gui_error = GUIError(entry, duplicate['location'], error)
                        if gui_error not in self.issue_list:
                            self.issue_list.append(gui_error)
        self.render()
        

if __name__ == "__main__":

    root = tk.Tk()

    stop_event = threading.Event()
    def on_close():
        stop_event.set()
        fm.save()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.geometry("500x300")
    # root.minsize(500, 300)
    f = tk.Frame(root)
    fm = FileManager()
    fm.load()

    infoWidget = InfoWidget(root)
    infoWidget.updateErrors(fm)

    def update(stop_event:threading.Event):
        while True:
            if fm.process():
                infoWidget.updateErrors(fm)

            if(stop_event.is_set()):
                return False
    
    
    update_thread = threading.Thread(target=update, args=[stop_event])
    update_thread.start()

    btn_frame = tk.Frame(root, padx=5, pady=5)
    toggle = tk.Checkbutton(btn_frame, text="Auto Gather")
    btn = tk.Button(btn_frame, text="Gather ALL NC", padx=20, pady=20, width=10)
    btn2 = tk.Button(btn_frame, text="Gather ALL ASC", padx=20, pady=20, width=10)

    toggle.pack(side=tk.TOP)
    btn.pack(fill=tk.X, side=tk.TOP)
    btn2.pack(fill=tk.X, side=tk.TOP)

    btn_frame.grid(row=0, column=0, sticky='nsew')
    infoWidget.grid(row=0, column=1, sticky='nsew')

    root.grid_columnconfigure(0, weight=0)
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)
    root.mainloop()