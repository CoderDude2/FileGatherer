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

ErrorType = Enum('IssueType',[
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
    file_mtime:float = None
    errors:list[ErrorType] = field(default_factory=list)

    def add_error(self, error:ErrorType):
        if error not in self.errors:
            self.errors.append(error)
    
    def full_path(self):
        return os.path.join(self.location, self.file_name)

    @classmethod
    def from_path(cls, path):
        fileData = cls()
        fileData.file_name = os.path.basename(path).lower()
        fileData.location = os.path.dirname(path)
        fileData.file_mtime = os.stat(path).st_mtime

        with open(path, 'r') as file:
            first_line = file.readline()
            contents = file.readlines()
        
        if 'ASC' in first_line:
            case_type = 'ASC'
        elif 'T-L' in first_line or 'TLCS' in first_line or 'TLOC' in first_line:
            case_type = "TLOC"
        elif 'AOT14' in first_line:
            case_type = "AOT"
        else:
            case_type = "DS"

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
            fileData.add_error(ErrorType.SUBPROGRAM_0_ERR)
        if not contains_subprogram_1:
            fileData.add_error(ErrorType.SUBPROGRAM_1_ERR)
        if not contains_subprogram_2:
            fileData.add_error(ErrorType.SUBPROGRAM_2_ERR)
        
        difference = round(math.fabs(part_length - cut_off), 4)
        if difference > 0.01:
            fileData.add_error(ErrorType.PART_LENGTH_ERR)

        if not prg_regex.match(fileData.file_name):
            fileData.add_error(ErrorType.INVALID_NAME_ERR)

        if fileData.file_name == "4001.prg" and case_type == "ASC":
            fileData.add_error(ErrorType.INVALID_NAME_ERR)

        return fileData

    def serialize_json(self):
        serialized_output = {
            'file_name':self.file_name,
            'location':self.location,
            'file_mtime':self.file_mtime,
            'errors':[e.value for e in self.errors],
        }
        return serialized_output

    @classmethod
    def deserialize_json(cls, json_string):
        file_name = json_string['file_name']
        location = json_string['location']
        file_mtime = json_string['file_mtime']
        errors = [ErrorType(e) for e in json_string]
        return cls(
            file_name,
            location,
            file_mtime,
            errors
        )

class FileManager:
    def __init__(self):  
        self.file_hashmap = {}

    def run(self):
        while True:
            self.remove_missing_files()
    
    def remove_missing_files(self): 
        keys_to_remove = []
        for key in self.file_hashmap.keys():
            entries:list[FileData] = self.file_hashmap[key]
            indices_to_remove = []
            for i, entry in enumerate(entries):
                if not os.path.exists(os.path.join(entry.location, entry.file_name)):
                    indices_to_remove.append(i)
            print(indices_to_remove)
            for index in indices_to_remove:
                self.file_hashmap[key].pop(index)
            if(len(self.file_hashmap[key]) == 0):
                keys_to_remove.append(key)
        
        print(keys_to_remove)
        for key in keys_to_remove:
            del(self.file_hashmap[key])
        
        print(self.file_hashmap)

    def scan_folder(self):
        for root, _, files in os.walk(gather_prg.REMOTE_PRG_PATH):
            if len(files) > 0 and "ALL" not in os.path.basename(root) and not asc_folder_regex.match(os.path.basename(root)):
                try:
                    for name in files:
                        file_entries = self.file_hashmap.get(name)

                        if file_entries:
                            entries_to_remove = []
                            for entry in file_entries:
                                if entry.location == root:
                                    print("Original", os.path.join(root, name))
                                else:
                                    print("Duplicate", os.path.join(root, name))
                        else:
                            data = FileData.from_path(os.path.join(root, name))
                            self.file_hashmap[name] = [data]
                            print(self.file_hashmap[name])

                        # if prg_regex.match(name):
                        #     if not self.file_hashmap.get(name):
                        #         data = FileData.from_path(os.path.join(root, name))
                        #         self.file_hashmap[name] = data
                        #         print(len(fm.file_hashmap.keys()))
                        #     else:
                        #         fd:FileData = self.file_hashmap[name]
                        #         f_stat = os.stat(os.path.join(root, name))

                        #         if fd.location == root:
                        #             if f_stat.st_mtime != fd.file_mtime:
                        #                 new_data = FileData.from_path(os.path.join(root, name))
                        #                 self.file_hashmap[name] = new_data
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
    fm.remove_missing_files()
    # fm.scan_folder()