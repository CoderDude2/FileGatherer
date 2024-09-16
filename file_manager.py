import os
import re
from enum import Enum
import math
import shutil
import time
from dataclasses import dataclass, field

import gather_prg

prg_regex = re.compile(r'(\d{4,})([A-Za-z.]+)')
asc_folder_regex = re.compile(r'\d+.\d+_ASC_\((\d+)\)')
folder_regex = re.compile(r'(\d+) ?\((\d+)?\) ?([A-Za-z\+ ]+)?')

IssueType = Enum('IssueType',[
    'SUBPROGRAM_0_ERR',
    'SUBPROGRAM_1_ERR',
    'SUBPROGRAM_2_ERR',
    'INVALID_NAME_ERR',
    'DUPLICATE_PRG_ERR',
    'PART_LENGTH_ERR',
    'MISSING_UG_VALUES_ERR'])
    
@dataclass
class Issue:
    issue_type:IssueType
    message:str

    def __eq__(self, other):
        return (self.issue_type == other.issue_type)

@dataclass
class FileData:
    file_name:str = None
    location:str = None
    file_stat:os.stat_result = None
    case_type:str = None
    issues:list[Issue] = field(default_factory=list)
    part_length:float = 0
    cut_off:float = 0
    
    
    def add_issue(self, issue_type:IssueType, message:str):
        i = Issue(issue_type, message)
        if i not in self.issues:
            self.issues.append(i)

    def full_path(self):
        return os.path.join(self.location, self.file_name)

file_hashmap = {}

def get_file_data(path) -> FileData:
    fileData = FileData()
    fileData.file_name = os.path.basename(path).lower()

    fileData.location = os.path.dirname(path)
    fileData.file_stat = os.stat(path)

    with open(path, 'r') as file:
        first_line = file.readline()
        contents = file.readlines()
    
    if 'ASC' in first_line:
        fileData.case_type = 'ASC'
    elif 'T-L' in first_line or 'TLCS' in first_line or 'TLOC' in first_line:
        fileData.case_type = "TLOC"
    elif 'AOT14' in first_line:
        fileData.case_type = "AOT"
    else:
        fileData.case_type = "DS"

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
            fileData.part_length = float(contents[i+1].split(' ')[1])

        if "T0100 (CUT-OFF)" in line:
            fileData.cut_off = float(contents[i+2][4:])

    if not contains_subprogram_0: 
        fileData.add_issue(IssueType.SUBPROGRAM_0_ERR, f'Missing Subprogram: $0')
    if not contains_subprogram_1:
        fileData.add_issue(IssueType.SUBPROGRAM_1_ERR, f'Missing Subprogram: $1')
    if not contains_subprogram_2:
        fileData.add_issue(IssueType.SUBPROGRAM_2_ERR, f'Missing Subprogram: $2')
    
    difference = round(math.fabs(fileData.part_length - fileData.cut_off), 4)
    if difference > 0.01:
        fileData.add_issue(IssueType.PART_LENGTH_ERR, f'PART-LENGTH and CUT-OFF differ by {difference}')

    if not prg_regex.match(fileData.file_name):
        fileData.add_issue(IssueType.INVALID_NAME_ERR, message=f'{fileData.file_name} name is invalid')

    if fileData.file_name == "4001.prg" and fileData.case_type == "ASC":
        fileData.add_issue(IssueType.INVALID_NAME_ERR, f'{fileData.file_name} name is invalid for ASC case.')

    return fileData

for root, dirs, files in os.walk(gather_prg.REMOTE_PRG_PATH):
    if len(files) > 0 and "ALL" not in os.path.basename(root) and not asc_folder_regex.match(os.path.basename(root)):
        for name in files:
            data = get_file_data(os.path.join(root, name))

            if file_hashmap.get(name):
                file_hashmap[name].append(data)
            else:
                file_hashmap[name] = [data]
            
            print(data)

# for key in file_hashmap:
#     print(key, file_hashmap[key])

# print(file_data(r"\\192.168.1.100\Trubox\####ERP_RM####\Y2024\M09\D13\1. CAM\3. NC files\Sulgi\4643.prg"))