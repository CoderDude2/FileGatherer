import os
import re
from enum import Enum
import math

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
                                print(len(self.processed_files.keys()))
                            else:
                                existing_duplicates = []
                                for duplicate in self.processed_files[name]['duplicates']:
                                    if os.path.exists(os.path.join(duplicate['location'], name)):
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
    
    def get_files_with_errors(self):
        pass


if __name__ == "__main__":
    fm = FileManager()
    fm.process()
    print(fm.processed_files)