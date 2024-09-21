import os
import re
from enum import Enum
import math
import json
from dataclasses import dataclass, field
import time


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
class FileData:
    file_name:str = None
    location:str = None
    file_inode:int = None
    file_mtime:float = None
    case_type:str = None
    issues:list[IssueType] = field(default_factory=list)
    part_length:float = 0
    cut_off:float = 0
    
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    def add_issue(self, issue_type:IssueType):
        if issue_type not in self.issues:
            self.issues.append(issue_type)

    def full_path(self):
        return os.path.join(self.location, self.file_name)

    @classmethod
    def from_path(cls, path):
        fileData = cls()
        fileData.file_name = os.path.basename(path).lower()

        fileData.location = os.path.dirname(path)
        stat_result = os.stat(path)
        fileData.file_inode = stat_result.st_ino
        fileData.file_mtime = stat_result.st_mtime

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
            fileData.add_issue(IssueType.SUBPROGRAM_0_ERR)
        if not contains_subprogram_1:
            fileData.add_issue(IssueType.SUBPROGRAM_1_ERR)
        if not contains_subprogram_2:
            fileData.add_issue(IssueType.SUBPROGRAM_2_ERR)
        
        difference = round(math.fabs(fileData.part_length - fileData.cut_off), 4)
        if difference > 0.01:
            fileData.add_issue(IssueType.PART_LENGTH_ERR)

        if not prg_regex.match(fileData.file_name):
            fileData.add_issue(IssueType.INVALID_NAME_ERR)

        if fileData.file_name == "4001.prg" and fileData.case_type == "ASC":
            fileData.add_issue(IssueType.INVALID_NAME_ERR)

        return fileData

    def serialize_json(self):
        serialized_output = {
            'file_name':self.file_name,
            'location':self.location,
            'file_inode':self.file_inode,
            'file_mtime':self.file_mtime,
            'case_type':self.case_type,
            'issues':[issue.value for issue in self.issues],
            'part_length':self.part_length,
            'cut_off':self.cut_off
        }
        return serialized_output

    @classmethod
    def deserialize_json(cls, json_string):
        file_name = json_string['file_name']
        location = json_string['location']
        file_inode = json_string['file_inode']
        file_mtime = json_string['file_mtime']
        case_type = json_string['case_type']
        issues = [IssueType(issue) for issue in json_string['issues']]
        part_length = json_string['part_length']
        cut_off = json_string['cut_off']
        return cls(
            file_name,
            location,
            file_inode,
            file_mtime,
            case_type,
            issues,
            part_length,
            cut_off
        )

def check_file(path) -> list[IssueType]:
    issues:list[IssueType] = []

    file_name = os.path.basename(path).lower()

    with open(path, 'r') as file:
        first_line = file.readline()
        contents = file.readlines()

    if 'ASC' in first_line:
        case_type = 'ASC'
    elif 'T-L' in first_line or 'TLCS' in first_line or 'TLOC' in first_line:
        case_type = 'TLOC'
    elif 'AOT14' in first_line:
        case_type = 'AOT'
    else:
        case_type = 'DS'

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

        if "T0100 (CUT-OFF)" in line:
            cut_off = float(contents[i+2][4:])

    if not contains_subprogram_0: 
        issues.append(IssueType.SUBPROGRAM_0_ERR)
    if not contains_subprogram_1:
        issues.append(IssueType.SUBPROGRAM_1_ERR)
    if not contains_subprogram_2:
        issues.append(IssueType.SUBPROGRAM_2_ERR)

    difference = round(math.fabs(part_length - cut_off), 4)
    if difference > 0.01:
        issues.append(IssueType.PART_LENGTH_ERR)

    if not prg_regex.match(file_name):
        issues.append(IssueType.INVALID_NAME_ERR)

    if file_name == "4001.prg" and case_type == "ASC":
        issues.append(IssueType.INVALID_NAME_ERR)

    return issues

class FileManager:
    def __init__(self):
        self.processed_files = {}
    
    def process(self):
        for root, _, files in os.walk(gather_prg.REMOTE_PRG_PATH):
            if len(files) > 0 and "ALL" not in os.path.basename(root) and not asc_folder_regex.match(os.path.basename(root)):
                for name in files:
                    if name != ".DS_Store":
                        f_stat = os.stat(os.path.join(root, name))
                        if name not in self.processed_files.keys():
                            self.processed_files[name] = {'location':root, 'mtime':f_stat.st_mtime, 'errors':check_file(os.path.join(root, name))}
                            print(len(self.processed_files.keys()))
                        else:
                            if self.processed_files[name]['mtime'] != f_stat.st_mtime and self.processed_files[name]['location'] == root:
                                self.processed_files[name] = {'location':root, 'mtime':f_stat.st_mtime, 'errors':check_file(os.path.join(root, name))}
                            elif self.processed_files[name]['location'] != root:
                                print("Duplicate File:", os.path.join(root, name))
    
    def get_files_with_errors(self):
        pass


if __name__ == "__main__":
    fm = FileManager()
    fm.process()
    print(fm.processed_files)