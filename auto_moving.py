from os import stat, replace
from os.path import dirname
from shutil import copy2, move
from datetime import datetime
from time import time
from common_functions import *


def main(settings):
    directory_with_scanned_directories = settings['directory_with_scanned_directories']
    path_to_the_logs_folder = settings['path_to_the_logs_folder']
    logs = []

    for path_settings in settings['directories']:
        if exists(path_settings['input']):
            if not(exists(path_settings['output'])):
                makedirs(path_settings['output'], exist_ok=True)

            current_time = time()
            file_name_exceptions = path_settings['file_name_exceptions']
            directory_name_exceptions = path_settings['directory_name_exceptions']

            directories_data = {}
            log = {
                "input": path_settings['input'],
                "output": path_settings['output'],
                "error_messages": [],
                "copy_messages": [],
                "move_messages": []
            }

            update_dir_info(current_time, directory_with_scanned_directories, path_settings['input'], directories_data)
            checking_the_condition_for_action(current_time, path_settings, file_name_exceptions, directory_name_exceptions, directories_data)

            if path_settings['copy']:
                log["copy_messages"] = []
                copy_files(current_time, path_settings, directories_data, log)
            else:
                log["move_messages"] = []
                moving_files(current_time, path_settings, directories_data, log)


            if path_settings['save_logs']:
                if log['error_messages'] or log['copy_messages'] or log['move_messages']:
                    if not log['copy_messages']:
                        del log['copy_messages']

                    if not log['error_messages']:
                        del log['error_messages']

                    if not log['move_messages']:
                        del log['move_messages']

                    logs.append(log)

    if logs:
        save_logs(current_time, path_to_the_logs_folder, 'auto_moving', logs)


def sorting_with_date(string_datetime, setup, destination_directory_path):
    def append_time_str(string_datetime, destination_directory_path, period):
        if period == 'Y':
            name = str(string_datetime.strftime('%Y'))
        elif period == 'm':
            name = str(string_datetime.strftime('%m'))
        elif period == 'd':
            name = str(string_datetime.strftime('%d'))
        elif period == 'Ym':
            name = str(string_datetime.strftime('%Y-%m'))
        elif period == 'Ymd':
            name = str(string_datetime.strftime('%Y-%m-%d'))

        destination_directory_path = join(destination_directory_path, name)

        return destination_directory_path

    if setup['sort_by_year']:
        destination_directory_path = append_time_str(string_datetime, destination_directory_path, 'Y')

        if setup['sort_by_month']:
            destination_directory_path = append_time_str(string_datetime, destination_directory_path, 'm')

            if setup['sort_by_days']:
                destination_directory_path = append_time_str(string_datetime, destination_directory_path, 'd')
        elif setup['sort_by_days']:
            destination_directory_path = append_time_str(string_datetime, destination_directory_path, 'md')
    else:
        if setup['sort_by_month']:
            destination_directory_path = append_time_str(string_datetime, destination_directory_path, 'Ym')

            if setup['sort_by_days']:
                destination_directory_path = append_time_str(string_datetime, destination_directory_path, 'd')
        elif setup['sort_by_days']:
            destination_directory_path = append_time_str(string_datetime, destination_directory_path, 'Ymd')

    return destination_directory_path


def copy_files(current_time, path_settings, directories_data, log):
    save_folders = path_settings['save_folders']
    sort_by_date = path_settings['sorting_with_date']['sort_by_days'] or path_settings['sorting_with_date']['sort_by_month'] or path_settings['sorting_with_date']['sort_by_year']
    len_input_path = len(path_settings['input']) + 1
    string_datetime = datetime.fromtimestamp(current_time)

    for directory_path, directory_info in directories_data.items():
        for file_path, move_file in directory_info['files'].items():
            if move_file:
                if save_folders:
                    if sort_by_date:
                        if path_settings['sorting_with_date']['in_the_root_folder']:
                            destination_directory_path = sorting_with_date(string_datetime, path_settings['sorting_with_date'], path_settings['output'])
                            destination_directory_path = join(destination_directory_path, directory_path[len_input_path:])
                        else:
                            destination_directory_path = join(path_settings['output'], directory_path[len_input_path:])
                            destination_directory_path = sorting_with_date(string_datetime, path_settings['sorting_with_date'], destination_directory_path)
                    else:
                        destination_directory_path = join(path_settings['output'], directory_path[len_input_path:])
                else:
                    destination_directory_path = path_settings['output']

                    if sort_by_date:
                        destination_directory_path = sorting_with_date(string_datetime, path_settings['sorting_with_date'], destination_directory_path)

                destination_directory_path = join(destination_directory_path, basename(file_path))
                flag = False

                if not exists(destination_directory_path):
                    flag = True
                elif path_settings['overwrite_files']:
                    file1_stat = stat(file_path)
                    file2_stat = stat(destination_directory_path)

                    if not(file1_stat.st_size == file2_stat.st_size and file1_stat.st_mtime == file2_stat.st_mtime):
                        flag = True

                if flag:
                    if file_path != destination_directory_path:
                        makedirs(dirname(destination_directory_path), exist_ok=True)

                        try:
                            copy2(file_path, destination_directory_path)
                            print(f"Copy file {file_path} to {dirname(destination_directory_path)}")
                            message = {"old_path": file_path, "new_path": destination_directory_path}
                            log['copy_messages'].append(message)
                        except Exception as error:
                            print(error)
                            message = {"old_path": file_path, "new_path": destination_directory_path, "error": str(error)}
                            log['error_messages'].append(message)


def moving_files(current_time, path_settings, directories_data, log):
    save_folders = path_settings['save_folders']
    sort_by_date = path_settings['sorting_with_date']['sort_by_days'] or path_settings['sorting_with_date']['sort_by_month'] or path_settings['sorting_with_date']['sort_by_year']
    len_input_path = len(path_settings['input']) + 1
    string_datetime = datetime.fromtimestamp(current_time)

    for directory_path, directory_info in directories_data.items():
        for file_path, move_file in directory_info['files'].items():
            if move_file:
                if save_folders:
                    if sort_by_date:
                        if path_settings['sorting_with_date']['in_the_root_folder']:
                            destination_directory_path = sorting_with_date(string_datetime, path_settings['sorting_with_date'], path_settings['output'])
                            destination_directory_path = join(destination_directory_path, directory_path[len_input_path:])
                        else:
                            destination_directory_path = join(path_settings['output'], directory_path[len_input_path:])
                            destination_directory_path = sorting_with_date(string_datetime, path_settings['sorting_with_date'], destination_directory_path)
                    else:
                        destination_directory_path = join(path_settings['output'], directory_path[len_input_path:])
                else:
                    destination_directory_path = path_settings['output']

                    if sort_by_date:
                        destination_directory_path = sorting_with_date(string_datetime, path_settings['sorting_with_date'], destination_directory_path)

                destination_directory_path = join(destination_directory_path, basename(file_path))

                if not exists(destination_directory_path) or path_settings['overwrite_files']:
                    if file_path != destination_directory_path:
                        makedirs(dirname(destination_directory_path), exist_ok=True)

                        try:
                            replace(file_path, destination_directory_path)
                            print(f"Moved file {file_path} to {dirname(destination_directory_path)}")
                            message = {"old_path": file_path, "new_path": destination_directory_path}
                            log['move_messages'].append(message)
                        except Exception:
                            try:
                                move(file_path, destination_directory_path)
                                print(f"Moved file {file_path} to {dirname(destination_directory_path)}")
                                message = {"old_path": file_path, "new_path": destination_directory_path}
                                log['error_messages'].append(message)
                            except Exception as error:
                                print(error)
                                message = {"old_path": file_path, "new_path": destination_directory_path, "error": str(error)}
                                log['error_messages'].append(message)


SETTING_PATH = ''

with open(SETTING_PATH, 'r', encoding = 'UTF-8') as json_file:
    settings = load(json_file)

main(settings)
