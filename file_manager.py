import os
import re
import enum
from dataclasses import dataclass


asc_folder_regex = re.compile(r'\d+.\d+_ASC_\((\d+)\)')
folder_regex = re.compile(r'(\d+) ?\((\d+)?\) ?([A-Za-z\+ ]+)?')

class IssueType(enum.Enum):
    SUBPROGRAM_ERR=1
    INVALID_NAME_ERR=2
    DUPLICATE_PRG=3

@dataclass
class FileData:
    locations:list[str]
    case_type:str
    issues:list[str]

file_hashmap = {}

def check(path):
    result = {
        "errors":[]
    }

    with open(path, 'r') as file:
        first_line = file.readline()
        contents = file.readlines()
    if 'ASC' in first_line:
        result['type'] = "ASC"
    elif 'T-L14' in first_line:
        result['type'] = "TLOC"
    elif 'AOT14' in first_line:
        result['type'] = "AOT"
    else:
        result['type'] = "DS"

    part_length = 0
    cut_off = 0
    contains_subprogram_0 = False
    contains_subprogram_1 = False
    contains_subprogram_2 = False

    for line in contents:
        if '$0' in line:
            contains_subprogram_0 = True
        
        if '$1' in line:
            contains_subprogram_1 = True
        
        if '$2' in line:
            contains_subprogram_2 = True
        
        if "#100=" in line:
            part_length = float(line.split(" ")[1])
            result["part_length"] = part_length

    if not contains_subprogram_0: 
        result['errors'].append((IssueType.SUBPROGRAM_ERR, "Missing $0 subprogram"))
    if not contains_subprogram_1:
        result['errors'].append((IssueType.SUBPROGRAM_ERR, "Missing $1 subprogram"))
    if not contains_subprogram_2:
        result['errors'].append((IssueType.SUBPROGRAM_ERR, "Missing $2 subprogram"))
    
    return result

for root, dirs, files in os.walk("./nc"):
    if len(files) > 0 and os.path.basename(root) != "ALL":
        for name in files:
            if name.split(".")[1] == "prg":
                if file_hashmap.get(name):
                    
                    file_hashmap[name]["locations"].append(root)
                    if len(file_hashmap[name]["locations"]) > 0:
                        file_hashmap[name]["data"]["errors"].append((IssueType.DUPLICATE_PRG, f"{name} also in {os.path.join(root, name)}"))
                else:
                    file_data = check(os.path.join(root,name))
                    file_hashmap[name] = {
                        "locations":[root],
                        "data":file_data
                        }

for i in file_hashmap:
    print(i, file_hashmap[i])