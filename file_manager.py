import datetime
import json
import math
import os
import re
from enum import Enum

import gather_prg

prg_regex = re.compile(r'(\d{4,})([A-Za-z.]+)')
asc_folder_regex = re.compile(r'\d+.\d+_ASC_\((\d+)\)')
folder_regex = re.compile(r'(\d+) ?\((\d+)?\) ?([A-Za-z\+ ]+)?')

def date_as_path(date=None):
    if(date == None):
        date = datetime.datetime.now().date()
    _day = f'D{"0"+str(date.day) if date.day < 10 else str(date.day)}'
    _month = f'M{"0"+str(date.month) if date.month < 10 else str(date.month)}'
    _year = f'Y{str(date.year)}'
    return os.path.join(_year, _month, _day)

REMOTE_PRG_PATH = fr'\\192.168.1.100\Trubox\####ERP_RM####\{date_as_path()}\1. CAM\3. NC files'

IssueType = Enum('IssueType',[
    'SUBPROGRAM_0_ERR',
    'SUBPROGRAM_1_ERR',
    'SUBPROGRAM_2_ERR',
    'INVALID_NAME_ERR',
    'DUPLICATE_PRG_ERR',
    'PART_LENGTH_ERR',
    'MISSING_UG_VALUES_ERR'])

def check_file(path) -> list[IssueType]:
    issues:list[IssueType] = []

    file_name = os.path.basename(path).lower()

    part_length = 0
    cut_off = 0

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

    contains_ug_101 = False
    contains_ug_102 = False
    contains_ug_103 = False
    contains_ug_104 = False
    contains_ug_105 = False

    for i, line in enumerate(contents):
        if '$0' in line:
            contains_subprogram_0 = True
        
        if '$1' in line:
            contains_subprogram_1 = True
        
        if '$2' in line:
            contains_subprogram_2 = True
        
        if "(PartLength)" in line:
            if "#100=" in contents[i+1]:
                if contents[i+1].split('=')[1].strip() != '':
                    part_length = float(contents[i+1].split('=')[1].strip())

        if "T0100 (CUT-OFF)" in line:
            cut_off = float(contents[i+2][4:])
        
        if "#101=" in line:
            contains_ug_101 = True
        
        if "#102=" in line:
            contains_ug_102 = True
        
        if "#103=" in line:
            contains_ug_103 = True
        
        if "#104=" in line:
            contains_ug_104 = True
        
        if "#105=" in line:
            contains_ug_105 = True

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

    if case_type == "ASC" or case_type == "TLOC" or case_type == "AOT":
        if not (contains_ug_101 and contains_ug_102 and contains_ug_103 and contains_ug_104 and contains_ug_105):
            issues.append(IssueType.MISSING_UG_VALUES_ERR)

    return issues

class FileManager:
    def __init__(self):
        self.processed_files = {}
    
    def process(self) -> bool:
        updated = False

        keys_to_remove = []
        for key in self.processed_files:
            entry = self.processed_files[key]
            if not os.path.exists(os.path.join(entry['location'], key)):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del(self.processed_files[key])
            print(key, "Deleted")
            updated = True

        for root, dirs, files in os.walk(gather_prg.REMOTE_PRG_PATH):
            if "ALL" not in os.path.basename(root) and not asc_folder_regex.match(os.path.basename(root)):
                for name in files:
                    if '.prg' in name.lower():
                        try:
                            f_stat = os.stat(os.path.join(root, name))
                            if name not in self.processed_files.keys():
                                self.processed_files[name] = {'location':root, 'mtime':f_stat.st_mtime, 'errors':check_file(os.path.join(root, name)), 'duplicates':[]}
                                updated = True
                            else:
                                # Remove any duplicates that no longer exist
                                existing_duplicates = []
                                for duplicate in self.processed_files[name]['duplicates']:
                                    if os.path.exists(os.path.join(duplicate['location'], name)) and duplicate['location'] != self.processed_files[name]['location']:
                                        existing_duplicates.append(duplicate)
                                
                                if len(existing_duplicates) != len(self.processed_files[name]['duplicates']):
                                    self.processed_files[name] = {'location':root, 'mtime':f_stat.st_mtime, 'errors':check_file(os.path.join(root, name)), 'duplicates':existing_duplicates}
                                    updated = True
                                if self.processed_files[name]['mtime'] != f_stat.st_mtime and self.processed_files[name]['location'] == root:
                                    self.processed_files[name] = {'location':root, 'mtime':f_stat.st_mtime, 'errors':check_file(os.path.join(root, name)), 'duplicates':self.processed_files[name]['duplicates']}
                                    updated = True
                                elif self.processed_files[name]['location'] != root:
                                    duplicate_file = {'location':root, 'mtime':f_stat.st_mtime, 'errors':check_file(os.path.join(root, name))}
                                    duplicate_file['errors'].append(IssueType.DUPLICATE_PRG_ERR)
                                    if duplicate_file not in self.processed_files[name]['duplicates']:
                                        self.processed_files[name]['duplicates'].append(duplicate_file)
                                        updated = True
                        except PermissionError:
                            print(f"File: {name}, is open in another process.")
                        except FileNotFoundError:
                            print("Could not find the file", name)
        return updated
    
    def gather_valid_files(self, filter:str, dst:str):
        for key, value in self.processed_files.items():
            with open(os.path.join(value['location'], key)) as file:
                line = file.readline()
                if len(value['errors']) == 0:
                    print(line, "is valid")
    
    def save(self):
        serialized_processed_files = {}

        for key, entry in self.processed_files.items():
            location = entry['location']
            mtime = entry['mtime']
            errors = [error.value for error in entry['errors']]
            serialized_duplicates = []
            
            for duplicate in entry['duplicates']:
                duplicate_location = duplicate['location']
                duplicate_mtime = duplicate['mtime']
                duplicate_errors = [error.value for error in duplicate['errors']]
                serialized_duplicate = {'location':duplicate_location, 'mtime':duplicate_mtime, 'errors':duplicate_errors}
                serialized_duplicates.append(serialized_duplicate)

            serialized_processed_files[key] = {'location':location, 'mtime':mtime, 'errors':errors, 'duplicates':serialized_duplicates}
        with open('data.json', 'w+') as file:
            file.write(json.dumps(serialized_processed_files, indent=2))

    def load(self):
        if os.path.exists('data.json'):
            with open('data.json', 'r') as file:
                contents = file.read()
            json_data = json.loads(contents)

            for key, entry in json_data.items():
                deserialized_location = entry['location']
                deserialized_mtime = entry['mtime']
                deserialized_errors = [IssueType(i) for i in entry['errors']]
                deserialized_duplicates = []

                for duplicate in entry['duplicates']:
                    deserialized_duplicate_location = duplicate['location']
                    deserialized_duplicate_mtime = duplicate['mtime']
                    deserialized_duplicate_errors = [IssueType(i) for i in duplicate['errors']]
                    deserialized_duplicate = {'location':deserialized_duplicate_location, 'mtime':deserialized_duplicate_mtime, 'errors':deserialized_duplicate_errors}
                    deserialized_duplicates.append(deserialized_duplicate)
                
                deserialized_entry = {'location':deserialized_location, 'mtime':deserialized_mtime, 'errors':deserialized_errors, 'duplicates':deserialized_duplicates}
                self.processed_files[key] = deserialized_entry
        else:
            self.processed_files = {}

if __name__ == "__main__":
    fm = FileManager()
    fm.load()
    fm.gather_valid_files('ASC', '.')
    # for key, value in fm.processed_files.items():
    #     print(key, value)
    # fm.process()
    # fm.save()
    