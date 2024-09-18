import os
import re
from enum import Enum
import math
import json
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
    
    def serialize_json(self):
        serialized_issue = {
            'issue_type':self.issue_type.value,
            'message':self.message
        }
        return serialized_issue

    @classmethod
    def deserialize_json(cls, json_string):
        issue_type = IssueType(json_string['issue_type'])
        message = json_string['message']
        return cls(issue_type, message)

@dataclass
class FileData:
    file_name:str = None
    location:str = None
    file_inode:int = None
    file_mtime:float = None
    case_type:str = None
    issues:list[Issue] = field(default_factory=list)
    part_length:float = 0
    cut_off:float = 0
    
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    def add_issue(self, issue_type:IssueType, message:str):
        i = Issue(issue_type, message)
        if i not in self.issues:
            self.issues.append(i)

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

    def serialize_json(self):
        serialized_output = {
            'file_name':self.file_name,
            'location':self.location,
            'file_inode':self.file_inode,
            'file_mtime':self.file_mtime,
            'case_type':self.case_type,
            'issues':[issue.serialize_json() for issue in self.issues],
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
        issues = [Issue.deserialize_json(issue) for issue in json_string['issues']]
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

class FileManager:
    def __init__(self):  
        self.file_hashmap = {}
        self.load()
    
    def scan_folder(self):
        for root, _, files in os.walk(gather_prg.REMOTE_PRG_PATH):
            if len(files) > 0 and "ALL" not in os.path.basename(root) and not asc_folder_regex.match(os.path.basename(root)):
                try:
                    for name in files:
                        if not self.file_hashmap.get(name):
                            data = FileData.from_path(os.path.join(root, name))
                            self.file_hashmap[name] = data
                            print(len(fm.file_hashmap.keys()))
                        else:
                            fd:FileData = self.file_hashmap[name]
                            f_stat = os.stat(os.path.join(root, name))

                            if fd.location == root:
                                if f_stat.st_mtime != fd.file_mtime:
                                    new_data = FileData.from_path(os.path.join(root, name))
                                    self.file_hashmap[name] = new_data
                except PermissionError:
                    print('Permission Denied')

    def save(self):
        keys_to_remove = []
        for key,value in self.file_hashmap.items():
            if not os.path.exists(os.path.join(value.location, value.file_name)):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del(self.file_hashmap[key])

        serialized_output = {
            'file_hashmap':{

            }
        }

        for key in self.file_hashmap.keys():
            serialized_output['file_hashmap'][key] = self.file_hashmap[key].serialize_json()
        json_string = json.dumps(serialized_output, indent=' ')

        with open('data.json', 'w+') as file:
            file.write(json_string)

    def load(self):
        with open('data.json', 'r') as file:
            content = file.read()
        
        loaded_json = json.loads(content)
        self.file_hashmap = loaded_json['file_hashmap']
        for i in self.file_hashmap.keys():
            self.file_hashmap[i] = FileData.deserialize_json(self.file_hashmap[i])

if __name__ == "__main__":
    fm = FileManager()
    try:
        while True:
            fm.scan_folder()
    except KeyboardInterrupt:
        fm.save()