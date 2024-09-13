import tkinter as tk
import gather_prg
import threading
import time

class App(tk.Tk):
  def __init__(self):
    super().__init__()
    self.geometry("200x200")
    self.title("File Gather")
    self.protocol("WM_DELETE_WINDOW", self.on_close)

    self.grid_columnconfigure(0, weight=1)
    self.grid_rowconfigure(1, weight=1)
    self.grid_rowconfigure(2, weight=1)

    self.auto_check = tk.BooleanVar()

    self.auto_gather_checkbutton = tk.Checkbutton(master=self, text="Auto Gather", variable=self.auto_check, onvalue=True, offvalue=False, command=self.on_auto_gather_toggle)
    self.gather_prg_button = tk.Button(master=self, text="Gather All NC", command=gather_prg.gather_prg)
    self.gather_asc_button = tk.Button(master=self, text="Gather All ASC", command=gather_prg.gather_asc)

    self.auto_gather_checkbutton.grid(row=0, column=0, sticky='nsew')
    self.gather_prg_button.grid(row=1, column=0, sticky='nsew')
    self.gather_asc_button.grid(row=2, column=0, sticky='nsew')

    self.stop_event = threading.Event()
    self.enabled_event = threading.Event()
    self.auto_gather_thread = threading.Thread(target=self.auto_gather, args=[gather_prg.REMOTE_PRG_PATH, self.stop_event, self.enabled_event])
    self.auto_gather_thread.start()
  
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
     self.destroy()

  def auto_gather(self, path, disable_event:threading.Event, enabled_event:threading.Event):
    while True:
      if(enabled_event.is_set()):
          gather_prg.gather_prg(path)
          gather_prg.gather_asc(path)
          time.sleep(1)
      if(disable_event.is_set()):
          return False

def main():
  app = App()
  app.mainloop()

if __name__ == "__main__":
   main()