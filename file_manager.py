import os
import re
import enum
import math
import shutil
import time
from dataclasses import dataclass

import gather_prg

prg_regex = re.compile(r'(\d{4,})([A-Za-z.]+)')
asc_folder_regex = re.compile(r'\d+.\d+_ASC_\((\d+)\)')
folder_regex = re.compile(r'(\d+) ?\((\d+)?\) ?([A-Za-z\+ ]+)?')

class IssueType(enum.Enum):
    SUBPROGRAM_ERR=1
    INVALID_NAME_ERR=2
    DUPLICATE_PRG=3
    PART_LENGTH_ERR=4
    MISSING_UG_VALUES_ERR=5
    


@dataclass
class Issue:
    issue_type:IssueType
    message:str

@dataclass
class FileData:
    file_name:str
    location:list[str]
    file_stat:os.stat_result
    case_type:str
    part_length:float
    cut_off:float
    issues:list[Issue]

file_hashmap = {}

def file_data(path):
    file_name = os.path.basename(path).lower()
    result = {
        "errors":[]
    }

    result['file_name'] = file_name
    result['location'] = os.path.dirname(path)
    result['ino'] = os.stat(path).st_ino
    result['st_mtime'] = os.stat(path).st_mtime

    with open(path, 'r') as file:
        first_line = file.readline()
        contents = file.readlines()
    if 'ASC' in first_line:
        result['type'] = "ASC"
        if file_name == "4001.prg":
            result['errors'].append((IssueType.INVALID_NAME_ERR, f'{file_name} name is invalid for ASC case.'))
    elif 'T-L14' in first_line or "T-L" in first_line or "TLCS" in first_line:
        result['type'] = "TLOC"
    elif 'AOT14' in first_line:
        result['type'] = "AOT"
    else:
        result['type'] = "DS"
    
    if not prg_regex.match(file_name):
        result['errors'].append((IssueType.INVALID_NAME_ERR, f'{file_name} name is invalid'))

    part_length = 0
    cut_off = 0
    contains_subprogram_0 = False
    contains_subprogram_1 = False
    contains_subprogram_2 = False

    for i, line in enumerate(contents):
        if '$0' in line:
            contains_subprogram_0 = True
        
        if '$1' in line:
            contains_subprogram_1 = True
        
        if '$2' in line:
            contains_subprogram_2 = True
        
        if "(PartLength)" in line:
            part_length = float(contents[i+1].split(' ')[1])
            result["part_length"] = part_length

        if "T0100 (CUT-OFF)" in line:
            cut_off = float(contents[i+2][4:])
            result["cut_off"] = cut_off

    if not contains_subprogram_0: 
        result['errors'].append((IssueType.SUBPROGRAM_ERR, "Missing $0 subprogram"))
    if not contains_subprogram_1:
        result['errors'].append((IssueType.SUBPROGRAM_ERR, "Missing $1 subprogram"))
    if not contains_subprogram_2:
        result['errors'].append((IssueType.SUBPROGRAM_ERR, "Missing $2 subprogram"))
    
    difference = round(math.fabs(part_length - cut_off), 4)
    if difference > 0.01:
        result['errors'].append((IssueType.PART_LENGTH_ERR, f"Part length and cut-off differ by {difference}"))

    return result

for root, dirs, files in os.walk(gather_prg.REMOTE_PRG_PATH):
    if len(files) > 0 and "ALL" not in os.path.basename(root) and not asc_folder_regex.match(os.path.basename(root)):
        for name in files:
            data = file_data(os.path.join(root, name))

            if file_hashmap.get(name):
                file_hashmap[name].append(data)
            else:
                file_hashmap[name] = [data]

# for root, dirs, files in os.walk(gather_prg.REMOTE_PRG_PATH):
#     if len(files) > 0 and "ALL" not in os.path.basename(root) and not asc_folder_regex.match(os.path.basename(root)):
#         for name in files:
#             if name.split(".")[1] == "prg":
#                 if file_hashmap.get(name):
                    
#                     if root not in file_hashmap[name]["locations"]:
#                         file_hashmap[name]["locations"].append(root)
                    
#                     if len(file_hashmap[name]["locations"]) > 1:
#                         if (IssueType.DUPLICATE_PRG, f"{name} also in {os.path.join(root, name)}") not in file_hashmap[name]["data"]["errors"]:
#                             file_hashmap[name]["data"]["errors"].append((IssueType.DUPLICATE_PRG, f"{name} also in {os.path.join(root, name)}"))
#                 else:
#                     file_data = check(os.path.join(root,name))
#                     file_hashmap[name] = {
#                         "locations":[root],
#                         "data":file_data
                        # }
for key in file_hashmap:
    print(key, file_hashmap[key])

# print(file_data(r"\\192.168.1.100\Trubox\####ERP_RM####\Y2024\M09\D13\1. CAM\3. NC files\Sulgi\4643.prg"))