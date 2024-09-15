import datetime
import os
import re
from dataclasses import dataclass

asc_folder_regex = re.compile(r"\d+.\d+_ASC_\((\d+)\)")

def date_as_path(date=None):
    if(date == None):
        date = datetime.datetime.now().date()
    _day = f'D{"0"+str(date.day) if date.day < 10 else str(date.day)}'
    _month = f'M{"0"+str(date.month) if date.month < 10 else str(date.month)}'
    _year = f'Y{str(date.year)}'
    return os.path.join(_year, _month, _day)

# REMOTE_PRG_PATH = fr'\\192.168.1.100\Trubox\####ERP_RM####\{date_as_path()}\1. CAM\3. NC files'
REMOTE_PRG_PATH="./nc"

@dataclass
class Entry:
    name:str
    prg_folder:str
    files:set = None

def xcopy(src:str, dst:str) -> None:
    if os.name == 'nt':
        os.system(f'echo F |xcopy /Y "{src}" "{dst}"')
    elif os.name == 'posix':
        os.system(f'cp "{src}" "{dst}"')

def get_asc_folder_from_path(path) -> str:
    asc_folder_name = None
    for file in os.listdir(path):
        if(asc_folder_regex.match(file) and os.path.isdir(os.path.join(path, file))):
            asc_folder_name = file
    return asc_folder_name

def update_asc_folder_name(path) -> None:
    if(get_asc_folder_from_path(path)):
        asc_folder_name= get_asc_folder_from_path(path)
        new_folder_name = f'{datetime.datetime.now().month}.{datetime.datetime.now().day}_ASC_({len(os.listdir(os.path.join(path, asc_folder_name)))})'

        try:
            os.rename(os.path.join(path, asc_folder_name), os.path.join(path, new_folder_name))
        except FileNotFoundError:
            print("File not found:", path)

def create_asc_folder(path, date=datetime.datetime.now()):
    if(get_asc_folder_from_path(path)):
        return
    os.mkdir(os.path.join(path, f'{date.month}.{date.day}_ASC_(0)'))

def gather_prg(path=REMOTE_PRG_PATH):
    processed_files = set()
    if("ALL" not in os.listdir(path)):
        os.mkdir(os.path.join(path, "ALL"))
    else:
        processed_files = set(os.listdir(os.path.join(path, "ALL")))
    
    with open("names.txt", 'r') as file:
        contents = file.read()
    
    contents = contents.split("\n")
    entries:list[Entry] = []

    for name in contents:
        entries.append(Entry(name, os.path.join(path, name), set()))
    
    try:
        for entry in entries:
            for dir in os.listdir(entry.prg_folder):
                dir = os.path.join(entry.prg_folder, dir)
                if os.path.isdir(dir):
                    for file in os.listdir(dir):
                        if os.path.isfile(os.path.join(dir, file)) and file.split(".")[1] == "prg":
                            if file not in processed_files:
                                xcopy(os.path.join(dir, file), 
                                      os.path.join(path, "ALL", file))
                                processed_files.add(file)
                            elif os.stat(os.path.join(dir, file)).st_mtime != os.stat(os.path.join(path, "ALL", file)).st_mtime:
                                xcopy(os.path.join(dir, file), 
                                      os.path.join(path, "ALL", file))
                        
                if os.path.isfile(dir):
                    file = os.path.split(dir)[1]
                    if file.split(".")[1] == "prg":
                        if file not in processed_files:
                            xcopy(os.path.join(dir), os.path.join(path, "ALL", file))
                            processed_files.add(file)
                        elif os.stat(os.path.join(dir)).st_mtime != os.stat(os.path.join(path, "ALL", file)).st_mtime:
                            xcopy(os.path.join(dir), os.path.join(path, "ALL", file))
    except (OSError, PermissionError, FileExistsError, FileNotFoundError) as e:
        pass
                    
def is_asc(file):
    try:
        with open(file, 'r') as f:
            contents = f.readline()
        first_line = contents.split("\n")[0]
        if("ASC" in first_line and "4001" not in first_line):
            return True
        return False
    except (FileNotFoundError, UnicodeDecodeError, PermissionError, OSError) as e:
        if(e == OSError):
            print("Contents:", contents)
            print("File:",file)
        return None

def gather_asc(path=REMOTE_PRG_PATH):
    
    asc_folder = get_asc_folder_from_path(path)

    if(not asc_folder):
        create_asc_folder(path)
        asc_folder = get_asc_folder_from_path(path)
    
    processed_files = set(os.listdir(os.path.join(path, asc_folder)))

    with open("names.txt", 'r') as file:
        contents = file.read()

    contents = contents.split("\n")
    entries:list[Entry] = []

    for name in contents:
        entries.append(Entry(name, os.path.join(path, name), set()))

    try:
        for entry in entries:
            for dir in os.listdir(entry.prg_folder):
                dir = os.path.join(entry.prg_folder, dir)
                if os.path.isdir(dir):
                    for file in os.listdir(dir):
                        if os.path.isfile(os.path.join(dir,file)) and is_asc(os.path.join(dir,file)) and file.split(".")[1] == "prg":
                            if file not in processed_files:
                                xcopy(os.path.join(dir, file), os.path.join(path, asc_folder, file))
                                processed_files.add(file)
                            elif os.stat(os.path.join(dir, file)).st_mtime != os.stat(os.path.join(path, asc_folder, file)).st_mtime:
                                xcopy(os.path.join(dir, file), os.path.join(path, asc_folder, file))      
                elif os.path.isfile(dir) and is_asc(dir):
                    file = os.path.split(dir)[1]
                    if file.split(".")[1] == "prg":
                        if file not in processed_files:
                            xcopy(os.path.join(dir), os.path.join(path, asc_folder, file))
                            processed_files.add(file)
                        elif os.stat(os.path.join(dir)).st_mtime != os.stat(os.path.join(path, asc_folder, file)).st_mtime:
                            xcopy(os.path.join(dir), os.path.join(path, asc_folder, file))
    except (OSError, PermissionError, FileExistsError, FileNotFoundError) as e:
        print(e)
        pass

    try:
        update_asc_folder_name(path)
    except PermissionError:
        print("ASC folder is opened in another process. Cannot rename.")

