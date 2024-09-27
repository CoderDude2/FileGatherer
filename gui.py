import tkinter as tk
import threading

import info_widget
import file_manager

class MenuBar(tk.Menu):
    def __init__(self, master=None):
        super().__init__(master)

        self.file_menu = tk.Menu(self, tearoff=False)
        self.file_menu.add_command(label='   Exit   ', command=master.on_close)

        self.help_menu = tk.Menu(self, tearoff=False)

        self.add_cascade(label='File', menu=self.file_menu)
        self.add_cascade(label='Help', menu=self.help_menu)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.fm = file_manager.FileManager()
        self.fm.load("data.json")
        self.fm.process()

        self.geometry("445x275")
        self.minsize(445, 275)

        self.title("File Gather")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.menu_bar = MenuBar(self)

        self.auto_check = tk.BooleanVar()

        self.control_frame = tk.Frame(master=self)
        self.auto_gather_checkbutton = tk.Checkbutton(master=self.control_frame, text="Auto Gather", variable=self.auto_check, onvalue=True, offvalue=False, command=self.on_auto_gather_toggle)
        self.gather_prg_button = tk.Button(master=self.control_frame, text="Gather All NC", command=self.gather_prg, padx=20, pady=20)
        self.gather_asc_button = tk.Button(master=self.control_frame, text="Gather All ASC", command=self.gather_asc, padx=20, pady=20)

        self.info_widget = info_widget.InfoWidget()
        self.info_widget.updateErrors(self.fm)

        self.auto_gather_checkbutton.pack(side=tk.TOP)
        self.gather_prg_button.pack(fill=tk.X, side=tk.TOP)
        self.gather_asc_button.pack(fill=tk.X, side=tk.TOP)

        self.control_frame.grid(row=0, column=0, sticky='nsew')
        self.info_widget.grid(row=0, column=1, sticky='nsew')

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.config(menu=self.menu_bar)

        self.stop_event = threading.Event()
        self.enabled_event = threading.Event()
        self.auto_gather_thread = threading.Thread(target=self.auto_gather, args=[self.stop_event, self.enabled_event])
        self.auto_gather_thread.start()

    def gather_prg(self):
        self.fm.copy_all_valid_files()

    def gather_asc(self):
        self.fm.copy_asc_files()

    def print_value(self):
        print(self.auto_check.get())

    def on_auto_gather_toggle(self):
        if(self.enabled_event.is_set()):
            self.enabled_event.clear()
            self.gather_prg_button.configure(state=tk.NORMAL)
            self.gather_asc_button.configure(state=tk.NORMAL)
        else:
            self.enabled_event.set()
            self.gather_prg_button.configure(state=tk.DISABLED)
            self.gather_asc_button.configure(state=tk.DISABLED)

    def on_close(self):
        self.stop_event.set()
        self.fm.save("data.json")
        self.destroy()

    def auto_gather(self, disable_event:threading.Event, enabled_event:threading.Event):
        while True:
            if self.fm.process():
                    self.info_widget.updateErrors(self.fm)
            if enabled_event.is_set():
                try:
                    self.fm.copy_all_valid_files()
                except (FileNotFoundError, UnicodeDecodeError, PermissionError, OSError) as e:
                    print(e, type(e))

                    
            if(disable_event.is_set()):
                return False

def main():
  app = App()
  app.mainloop()

if __name__ == "__main__":
   main()