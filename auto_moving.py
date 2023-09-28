import os
import time
import json
import shutil


def main(settings):
    directory_with_scanned_directories = settings['directory_with_scanned_directories']
    current_time = time.time()

    for path_settings in settings['directories']:
        directory_data = update_dir_info(current_time, directory_with_scanned_directories, path_settings['input'])
        directory_data = checking_the_condition_for_moving(current_time, path_settings, directory_data)
        moving(current_time, path_settings, directory_data)


def update_dir_info(current_time, directory_with_scanned_directories, directory_path): # Updating data about the contents of directories
    if not(os.path.exists(directory_path)):
        return {}

    correct_directory_path = directory_path.replace('/', '_').replace(':', '')
    directory_log_path = f"{directory_with_scanned_directories}/{correct_directory_path}.json"

    if os.path.exists(directory_log_path):
        try:
            with open(directory_log_path, 'r', encoding='utf-8') as file:
                archive_data = json.load(file)
        except Exception as err:
            print(err)
            archive_data = {}
    else:
        archive_data = {}

    new_data = directory_walk(current_time, directory_path, archive_data)

    try:
        with open(directory_log_path, 'w+', encoding='utf-8') as file:
            json.dump(new_data, file, indent=4)
    except Exception as err:
        print(err)

    return new_data


def directory_walk(current_time, root_directory_path, archive_data):
    new_data = {}

    for directory_path, sub_directories, file_names in os.walk(root_directory_path):
        try:
            archive_directory_data = archive_data.pop(directory_path)
            archive_directory_data = archive_directory_data['files']
        except Exception:
            archive_directory_data = {}

        new_directory_data = {
            'name': os.path.basename(directory_path),
            'files': {},
            'sub_directories': {}
        }

        new_directory_data['files'] = update_files_info(current_time, directory_path, file_names, archive_directory_data)

        for sub_directory_name in sub_directories:
            sub_directory_path = os.path.join(directory_path, sub_directory_name)
            new_directory_data['sub_directories'][sub_directory_path] = {}

        new_data[directory_path] = new_directory_data

    return new_data


def update_files_info(current_time, directory_path, file_names, archive_directory_data):
    new_files_data = {}

    for file_name in file_names:
        file_path = os.path.join(directory_path, file_name)

        try:
            archive_file_data = archive_directory_data.pop(file_path)
            file_first_seen_time = archive_file_data['file_first_seen_time']
        except Exception:
            file_first_seen_time = current_time

        try:
            file_modified_time = os.path.getmtime(file_path)
        except:
            file_modified_time = current_time

        new_files_data[file_path] = {
            "name": file_name,
            "file_modified_time": file_modified_time,
            "file_first_seen_time": file_first_seen_time
        }

    return new_files_data


def checking_the_condition_for_moving(current_time, path_settings, directory_data):
    file_name_exceptions = path_settings['file_name_exceptions']
    directory_name_exceptions = path_settings['directory_name_exceptions']
    time_limit_for_modified_time = current_time - path_settings['time_limit_for_modified_time']
    time_limit_for_first_seen = current_time - path_settings['time_limit_for_first_seen']
    move_by_last_modified = path_settings['move_by_last_modified']
    move_by_first_seen = path_settings['move_by_first_seen']

    for directory_path, directory_info in directory_data.items():
        if any(directory_name_exception in directory_info['name'] for directory_name_exception in directory_name_exceptions):
            directory_data = save_directory(directory_data, directory_path)
        else:
            new_files_info = {}

            for file_path, file_info in directory_info['files'].items():
                new_files_info[file_path] = False

                is_file_exception = any(file_name_exception in file_info['name'] for file_name_exception in file_name_exceptions)
                is_modified_time_condition = file_info['file_modified_time'] < time_limit_for_modified_time
                is_first_seen_condition = file_info['file_first_seen_time'] < time_limit_for_first_seen

                if not is_file_exception:
                    if move_by_last_modified and move_by_first_seen and is_modified_time_condition and is_first_seen_condition:
                        new_files_info[file_path] = True
                    elif move_by_last_modified and is_modified_time_condition:
                        new_files_info[file_path] = True
                    elif move_by_first_seen and is_first_seen_condition:
                        new_files_info[file_path] = True

            directory_data[directory_path]['files'] = new_files_info

    return directory_data


def save_directory(directory_data, directory_path):
    directory_data[directory_path]['files'] = {}

    for sub_directory_path in directory_data[directory_path]['sub_directories'].keys():
        directory_data = save_directory(directory_data, sub_directory_path)

    return directory_data


def moving(current_time, path_settings, directory_data):
    move_messages, copy_messages, error_messages = [], [], []

    if path_settings['copy']:
        move_messages, copy_messages, error_messages = copy_files(path_settings, directory_data)
    else:
        move_messages, copy_messages, error_messages = moving_files(path_settings, directory_data)

    save_logs(current_time, path_settings, move_messages, copy_messages, error_messages)


def copy_files(path_settings, directory_data):
    move_messages, copy_messages, error_messages = [], [], []
    save_folders = path_settings['save_folders']

    for directory_path, directory_info in directory_data.items():
        for file_path, move_file in directory_info['files'].items():
            if move_file:
                if save_folders:
                    originat_file_directory = file_path.split(path_settings['input'])[-1].strip(os.path.sep)
                    destination_directory_path = os.path.join(path_settings['output'], originat_file_directory)
                else:
                    destination_directory_path = os.path.join(path_settings['output'], os.path.basename(file_path))

                flag = False

                if not os.path.exists(destination_directory_path):
                    flag = True
                elif path_settings['overwrite_files']:
                    file1_stat = os.stat(file_path)
                    file2_stat = os.stat(destination_directory_path)

                    if not(file1_stat.st_size == file2_stat.st_size and file1_stat.st_mtime == file2_stat.st_mtime):
                        flag = True

                if flag:
                    os.makedirs(os.path.dirname(destination_directory_path), exist_ok=True)

                    try:
                        shutil.copy2(file_path, destination_directory_path)
                        message = f"Copy file {file_path} to {os.path.dirname(destination_directory_path)}"
                        print(message)
                        copy_messages.append(message)
                    except Exception as error:
                        print(error)
                        error_messages.append(str(error))

    return move_messages, copy_messages, error_messages


def moving_files(path_settings, directory_data):
    move_messages, copy_messages, error_messages = [], [], []
    save_folders = path_settings['save_folders']

    for directory_path, directory_info in directory_data.items():
        for file_path, move_file in directory_info['files'].items():
            if move_file:
                if save_folders:
                    originat_file_directory = file_path.split(path_settings['input'])[-1].strip(os.path.sep)
                    destination_directory_path = os.path.join(path_settings['output'], originat_file_directory)
                else:
                    destination_directory_path = os.path.join(path_settings['output'], os.path.basename(file_path))

                if not os.path.exists(destination_directory_path) or path_settings['overwrite_files']:
                    os.makedirs(os.path.dirname(destination_directory_path), exist_ok=True)

                    try:
                        os.replace(file_path, destination_directory_path)
                        message = f"Moved file {file_path} to {os.path.dirname(destination_directory_path)}"
                        print(message)
                        move_messages.append(message)
                    except Exception:
                        try:
                            shutil.move(file_path, destination_directory_path)
                            message = f"Moved file {file_path} to {os.path.dirname(destination_directory_path)}"
                            print(message)
                            move_messages.append(message)
                        except Exception as error:
                            print(error)
                            error_messages.append(str(error))

    return move_messages, copy_messages, error_messages


def save_logs(current_time, path_settings, move_messages, copy_messages, error_messages):
    if move_messages:
        if path_settings['saved_move_files_info_to_text']:
            save_results_to_files(
                os.path.join(settings['path_to_the_logs_folder'],
                f"automatic_movement_log {time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(current_time))}.txt"),
                path_settings['input'], move_messages
            )

    if copy_messages:
        if path_settings['saved_copy_files_info_to_text']:
            save_results_to_files(
                os.path.join(settings['path_to_the_logs_folder'],
                f"automatic_copying_log {time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(current_time))}.txt"),
                path_settings['input'], copy_messages
            )

    if error_messages:
        if path_settings['saved_error_message_directory_to_text'] :
            save_results_to_files(
                os.path.join(settings['path_to_the_logs_folder'],
                f"automatic_move_or_copy_error_log {time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(current_time))}.txt"),
                path_settings['input'], error_messages
            )


def save_results_to_files(path, directory_path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'a+', encoding = 'utf-8') as file:
        file.write(os.path.basename(directory_path) + '\n')

        for row in data:
            file.write(row + '\n')

        file.write('\n')


if __name__ == '__main__':
    SETTING_PATH = 'auto_moving_settings.json'

    with open(SETTING_PATH, 'r', encoding='utf-8') as json_file:
        settings = json.load(json_file)

    main(settings)
