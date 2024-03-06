import datetime
import os
import shutil
import time
import re

asc_folder_regex = re.compile("\d+.\d+_ASC_\((\d+)\)")

def get_asc_folder_from_path(path):
    asc_folder_name = None
    for file in os.listdir(path):
        if(asc_folder_regex.match(file)):
            asc_folder_name = file
    return asc_folder_name

def update_asc_folder_name(path):
    if(get_asc_folder_from_path(path)):
        asc_folder_name= get_asc_folder_from_path(path)
        new_folder_name = f'{datetime.datetime.now().month}.{datetime.datetime.now().day}_ASC_({len(os.listdir(os.path.join(path, asc_folder_name)))})'

        os.rename(os.path.join(path, asc_folder_name), os.path.join(path, new_folder_name))

def create_asc_folder(path, date=datetime.datetime.now()):
    if(get_asc_folder_from_path(path)):
        return
    os.mkdir(os.path.join(path, f'{date.month}.{date.day}_ASC_(0)'))

def date_as_path(date=None):
    if(date == None):
        date = datetime.datetime.now().date()
    _day = f'D{"0"+str(date.day) if date.day < 10 else str(date.day)}'
    _month = f'M{"0"+str(date.month) if date.month < 10 else str(date.month)}'
    _year = f'Y{str(date.year)}'
    return os.path.join(_year, _month, _day)

REMOTE_PRG_PATH = f"//192.168.1.100/Trubox/####ERP_RM####/{date_as_path()}/1. CAM/3. NC files/"

def gather_prg(path=REMOTE_PRG_PATH):
    processed_files = []
    if("ALL" not in os.listdir(path)):
        os.mkdir(os.path.join(path, "ALL"))
    else:
        processed_files = os.listdir(os.path.join(path, "ALL"))

    result = os.walk(path)
    for root, dirs, files in result:
        for name in files:
            if(name not in processed_files and ".prg" in name):
                processed_files.append(name)
                shutil.copy2(
                    os.path.join(root, name),
                    os.path.join(path, "ALL")
                    )

def is_asc(file):
    try:
        with open(file, 'r') as f:
            contents = f.readline()
        first_line = contents.split("\n")[0]
        if("ASC" in first_line and "4001" not in first_line):
            return True
        return False
    except (FileNotFoundError, UnicodeDecodeError, PermissionError) as e:
        return None

def gather_asc(path=REMOTE_PRG_PATH):
    if(get_asc_folder_from_path(path)):
        asc_folder = os.path.join(path, get_asc_folder_from_path(path))
        processed_files = os.listdir(asc_folder)

        result = os.walk(path)
        for root, dirs, files in result:
            for name in files:
                if(name not in processed_files and ".prg" in name):
                    if(is_asc(os.path.join(root, name))):
                        processed_files.append(name)
                        shutil.copy2(
                            os.path.join(root, name),
                            asc_folder
                            )
        update_asc_folder_name(path)
        