"""
Do NOT edit this file as it runs the evaluation methodology for the Trained Pokemon agents.
"""

import logging
import os
import subprocess
from pathlib import Path

import virtualenv
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

logging.basicConfig(level=logging.INFO)


def run_venv(upi, requirement_path, model_path, model_name):
    path = f"{os.path.expanduser('~')}/venv"
    venv_dir = os.path.join(path, f"{upi}")
    virtualenv.cli_run([venv_dir])

    python_bin = f"{path}/{upi}/bin/python3"

    cares_rl_path = f"{Path.home()}/workspace/cares_reinforcement_learning"

    command = (
        f". {venv_dir}/bin/activate && pip install -r {cares_rl_path}/requirements.txt"
    )
    os.system(command)

    command = f". {venv_dir}/bin/activate && pip install {cares_rl_path}"
    os.system(command)

    command = f". {venv_dir}/bin/activate && pip install -r {requirement_path}/requirements.txt"
    os.system(command)

    command = f". {venv_dir}/bin/activate && pip install {requirement_path}"
    os.system(command)

    p = subprocess.Popen(
        [
            python_bin,
            "evaluate.py",
            "--upi",
            upi,
            "--model_path",
            model_path,
            "--model_name",
            model_name,
            "--results_path",
            model_path,
        ]
    )

    exit_code = p.wait()
    print(f"Exit code: {exit_code} {upi}")


def read_folder(drive, title, file_id):
    folder = {}

    folder["title"] = title
    folder["files"] = {}
    folder["folders"] = []

    drive_list = drive.ListFile(
        {"q": f"'{file_id}' in parents and trashed=false"}
    ).GetList()

    for f in drive_list:
        if f["mimeType"] == "application/vnd.google-apps.folder":
            folder["folders"].append(read_folder(drive, f["title"], f["id"]))
        else:
            folder["files"][f["title"]] = {
                "id": f["id"],
                "title": f["title"],
                "title1": f["alternateLink"],
            }

    return folder


def print_folders(directory, tab=0):
    tabs = " " * tab

    for _, file in directory["files"].items():
        message = f"{tabs}File: {file['title']}, id: {file['id']}"
        print(f"{message}")

    for folder in directory["folders"]:
        message = f"{tabs}Folder: {folder['title']}"
        print(f"{message}")
        print_folders(folder, tab=tab + 5)


def main():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

    drive = GoogleDrive(gauth)

    # COMPSYS726 - Assignment 1 Folder
    primary_folder_id = "1OWORBjdzuJjPZYZoCKMs4hI3xemvcDzh"

    directory = read_folder(
        drive, "COMPSYS726 - Assignments", file_id=primary_folder_id
    )

    print_folders(directory)

    for folders in directory["folders"]:
        upi = folders["title"]
        print(f"Title: {upi}")

        files = folders["files"]
        requirements_id = files["requirements.txt"]["id"]
        brock_task_id = files["brock.py"]["id"]

        model_folder = folders["folders"][0]
        logging.info(f"{model_folder=}")

        requirement_path = f"{Path(__file__).parent.parent}"
        logging.info(f"{requirement_path=}")

        brock_path = f"{Path(__file__).parent.parent}/pyboy_environment/environments/pokemon/tasks"
        logging.info(f"{brock_path=}")

        results_path = f"{Path(__file__).parent.parent}/results/{upi}"
        logging.info(f"Saving data into: {results_path}")

        if not os.path.exists(results_path):
            os.makedirs(results_path)

        file = drive.CreateFile({"id": requirements_id})
        file.GetContentFile(f"{requirement_path}/requirements.txt")

        file = drive.CreateFile({"id": brock_task_id})
        file.GetContentFile(f"{brock_path}/brock.py")

        logging.info(f"{type(model_folder['files'])=}")

        for file_name, model_info in model_folder["files"].items():
            model_name = file_name.split("_")[0]
            logging.info(f"{file_name=}")
            logging.info(f"{model_info=}")
            logging.info(f"{model_name=}")
            file = drive.CreateFile({"id": model_info["id"]})

            model_path = f"{results_path}/models"
            if not os.path.exists(model_path):
                os.makedirs(model_path)
            file.GetContentFile(f"{model_path}/{file_name}")

        run_venv(upi, requirement_path, results_path, model_name)


if __name__ == "__main__":
    main()
