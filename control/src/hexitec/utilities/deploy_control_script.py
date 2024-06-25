"""Deploy Control side configuration files.

Christian Angelsen, STFC Detector Systems Software Group
"""

import shutil
import os


def create_dir(full_path):
    """Create directory (recursively) if not existent."""
    if not os.path.isdir(full_path):
        os.makedirs(full_path)


def find_top_dir():
    """'Find' top directory of source, install directories."""
    os.chdir("../../")
    parent_path = os.getcwd()
    return parent_path


def copy_files(source, destination):
    """Copy files from source to destination directory."""
    [shutil.copy(source+file, destination) for file in os.listdir(source)]


if __name__ == '__main__':
    origin_cwd = os.getcwd()
    base_path = find_top_dir()
    print("Ensuring config directory exist..")
    create_dir(base_path + "/install/config/control")

    assert os.path.isdir(base_path + "/install/config/data")
    assert os.path.isdir(base_path + "/install/config/control")

    print("Copy Control config files..")
    control_config_files_source = f"{origin_cwd}/control/config/"
    control_config_files_dest = f"{base_path}/install/config/control/"
    copy_files(control_config_files_source, control_config_files_dest)
    print("Deployment script completed.")
