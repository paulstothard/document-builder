#!/usr/bin/env python3
"""
Author: 
    Paul Stothard
"""

import argparse
from datetime import datetime
import filecmp
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import textwrap
import time
import uuid

required_major = 3
required_minor = 8

try:
    import dropbox
    import dropbox.exceptions

    dropbox_available = True
except ImportError:
    dropbox_available = False


def check_executables(executables, verbose=False):
    for executable, link in executables.items():
        if shutil.which(executable) is not None:
            if verbose:
                print(f"\033[92m{executable} is present\033[0m")  # Green text
        else:
            pretty_print_error(
                f"{executable} is not present. You can download it from {link}"
            )
            sys.exit(1)


def check_file_exists(file_path):
    if not os.path.isfile(file_path):
        pretty_print_error(f"File '{file_path}' does not exist.")
        return False
    return True


def check_folder_exists(folder_path):
    if not os.path.exists(folder_path):
        pretty_print_error(f"Folder '{folder_path}' does not exist.")
        return False
    return True


def clean_folder(folder_path):
    if not prompt_yes_no(
        f"Are you sure you want to delete all files in {folder_path}?", default=False
    ):
        return

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            pretty_print_error(f"Failed to delete {file_path}. Reason: {e}")


def copy_and_compress_data_folders(folders):
    source_folder = config["project_source_folder"]

    for folder_name in folders:
        new_file_generated = False
        output_data_folder = os.path.join(
            config["project_data_output_folder"], folder_name
        )

        for data_folder_name in ["data", "data_not_tracked"]:
            source_data_folder = os.path.join(
                source_folder, folder_name, data_folder_name
            )
            if os.path.exists(source_data_folder):
                visible_files = [
                    name
                    for name in os.listdir(source_data_folder)
                    if not name.startswith(".")
                ]
                if not visible_files:  # Skip if no visible files
                    continue
                # Create output_data_folder only if there are visible files
                os.makedirs(output_data_folder, exist_ok=True)
                for item in visible_files:
                    item_path = os.path.join(source_data_folder, item)
                    if os.path.isfile(item_path):
                        shutil.copy2(item_path, output_data_folder)
                    else:
                        shutil.copytree(
                            item_path,
                            os.path.join(output_data_folder, item),
                            dirs_exist_ok=True,
                        )
                new_file_generated = True

        if new_file_generated:
            with tarfile.open(f"{output_data_folder}.tar.gz", "w:gz") as tar:
                tar.add(
                    output_data_folder, arcname=os.path.basename(output_data_folder)
                )

            shutil.rmtree(output_data_folder)  # Remove the folder after compression


def copy_source_folders_to_markdown_output(folders):
    source_folder = config["project_source_folder"]

    for folder_name in folders:
        source_folder_path = os.path.join(source_folder, folder_name)
        markdown_output_folder = os.path.join(
            config["project_markdown_output_folder"], folder_name
        )

        # Create the output folder if it doesn't exist
        os.makedirs(markdown_output_folder, exist_ok=True)

        # Copy document.md
        shutil.copy2(
            os.path.join(source_folder_path, "document.md"), markdown_output_folder
        )

        # Copy includes folder
        shutil.copytree(
            os.path.join(source_folder_path, "includes"),
            os.path.join(markdown_output_folder, "includes"),
            dirs_exist_ok=True,
        )


def create_link_files(folders):
    data_output_folder = config["project_data_output_folder"]
    data_to_share_links_folder = config["project_data_to_share_links_folder"]
    os.makedirs(data_to_share_links_folder, exist_ok=True)

    for folder in folders:
        item_path = os.path.join(data_output_folder, f"{folder}.tar.gz")
        if os.path.exists(item_path):
            base_name = os.path.splitext(os.path.splitext(folder)[0])[
                0
            ]  # Remove all extensions
            link_file_path = os.path.join(
                data_to_share_links_folder, f"{base_name}.txt"
            )
            if not os.path.exists(link_file_path):
                open(link_file_path, "a").close()


def create_project(folder_path, include_example_documents=False):
    if os.path.exists(folder_path):
        pretty_print_error(f"Folder '{folder_path}' already exists.")
        sys.exit(1)

    os.makedirs(folder_path)

    subfolders = [
        "config",
        "logs",
        "data",
        "data_links",
        "final_documents",
        "html",
        "markdown",
        "build_includes",
        "pdf",
        "source",
    ]
    for subfolder in subfolders:
        os.makedirs(os.path.join(folder_path, subfolder))

    config_file_path = os.path.join(config["project_root"], "config", "config.json")
    if os.path.exists(config_file_path):
        shutil.copy2(config_file_path, os.path.join(folder_path, "config"))
    else:
        pretty_print_error("Config file cannot be copied.")

    with open(os.path.join(folder_path, "config", "config.json"), "r+") as f:
        config_data = json.load(f)

        config_data["project_id"] = str(uuid.uuid4())

        keys_to_update = [
            "project_root",
            "publish_folder_data",
            "publish_folder_html",
            "publish_folder_markdown",
            "publish_folder_pdf",
        ]
        for key in keys_to_update:
            if key in config_data:
                config_data[key] = os.path.join(folder_path, config_data[key])
        f.seek(0)
        json.dump(config_data, f, indent=4)
        f.truncate()

    for key, value in config.items():
        if isinstance(value, str) and key in [
            "project_pandoc_pdf_template",
            "project_pandoc_latex_header",
            "project_pandoc_css_file",
        ]:
            if check_file_exists(value):
                shutil.copy2(value, os.path.join(folder_path, "build_includes"))

    if include_example_documents:
        documents = ["document_one", "document_two", "document_three"]
        for document in documents:
            os.makedirs(os.path.join(folder_path, "source", document))

        for document in documents:
            os.makedirs(os.path.join(folder_path, "source", document, "data"))
            os.makedirs(
                os.path.join(folder_path, "source", document, "data_not_tracked")
            )
            os.makedirs(os.path.join(folder_path, "source", document, "includes"))
            formatted_document = document.replace("_", " ").capitalize()
            with open(
                os.path.join(folder_path, "source", document, "document.md"), "w"
            ) as f:
                f.write(f"# {formatted_document}\n")
                f.write("\n")  # Add a blank line at the end
            with open(
                os.path.join(folder_path, "source", document, "settings.yaml"), "w"
            ) as f:
                f.write("---\n")
                f.write(f'title: "Sample document"\n')
                f.write("author: [Your name here]\n")
                f.write("colorlinks: TRUE\n")
                f.write("code-block-font-size: \\footnotesize\n")
                f.write("...\n")

    pretty_print("Project created successfully.")


def create_timestamp_files(folders):
    build_logs_folder = config["project_build_logs_folder"]

    for folder in folders:
        folder_log_folder = os.path.join(build_logs_folder, folder)
        os.makedirs(folder_log_folder, exist_ok=True)
        timestamp_file = os.path.join(folder_log_folder, "timestamp.txt")
        with open(timestamp_file, "w") as f:
            f.write(str(time.time()))


def edit_markdown_includes(folders):
    markdown_output_folder = config["project_markdown_output_folder"]

    for folder in folders:
        markdown_file = os.path.join(markdown_output_folder, folder, "document.md")
        includes_dir = os.path.join(markdown_output_folder, folder, "includes")
        with open(markdown_file, "r+") as f:
            content = f.read()
            matches = re.findall(r"!\[.*\]\((.*\..*)\)", content)
            for match in matches:
                old_image_path = os.path.join(includes_dir, os.path.basename(match))
                if os.path.exists(old_image_path):
                    with open(old_image_path, "rb") as img_f:
                        bytes = img_f.read()  # read entire file as bytes
                        readable_hash = hashlib.md5(bytes).hexdigest()
                        # hash the bytes
                        new_image_name = f"{readable_hash}{os.path.splitext(match)[1]}"
                        new_image_path = os.path.join(includes_dir, new_image_name)
                        os.rename(old_image_path, new_image_path)
                    content = content.replace(
                        match, os.path.join("includes", new_image_name)
                    )
            f.seek(0)
            f.write(content)
            f.truncate()


def generate_assignment_markdown(folders):
    markdown_output_folder = config["project_markdown_output_folder"]

    for folder in folders:
        markdown_file = os.path.join(markdown_output_folder, folder, "document.md")

        # determine total marks
        with open(markdown_file, "r") as f:
            content = f.read()
            in_code_block = False
            total_marks = 0
            for line in content.splitlines():
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                elif not in_code_block:
                    match = re.match(r"^#+ (\d+) marks?", line, re.IGNORECASE)
                    if match:
                        total_marks += int(match.group(1))

        # insert total marks into document.md
        with open(markdown_file, "r+") as f:
            lines = f.readlines()
            f.seek(0)
            f.truncate()
            in_code_block = False
            marks_added = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                if not in_code_block and line.startswith("#") and not marks_added:
                    f.write(f"{line.rstrip()} ({total_marks} marks total)\n")
                    marks_added = True
                else:
                    f.write(line)

        # create copy of document with answers removed
        with open(markdown_file, "r") as f:
            content = f.read()
            lines = content.splitlines()
            new_lines = []
            in_code_block = False
            in_answer_block = False
            i = 0
            while i < len(lines):
                if lines[i].strip().startswith("```"):
                    in_code_block = not in_code_block
                if not in_code_block:
                    if re.match(r"^#+ answer", lines[i], re.IGNORECASE):
                        in_answer_block = True
                    elif re.match(r"^#+ question", lines[i], re.IGNORECASE):
                        in_answer_block = False
                if not in_answer_block and i < len(lines):
                    new_lines.append(lines[i])
                i += 1
            new_content = "\n".join(new_lines)

        with open(
            os.path.join(markdown_output_folder, folder, "document_to_share.md"),
            "w",
        ) as f:
            f.write(new_content)

        # create separate markdown files for each question, with the answers included
        with open(markdown_file, "r") as f:
            content = f.read()
            lines = content.splitlines()
            new_lines = []
            question_number = None
            in_code_block = False
            i = 0
            while i < len(lines):
                if lines[i].strip().startswith("```"):
                    in_code_block = not in_code_block
                if not in_code_block:
                    match = re.match(r"^#+ Question (\d+)", lines[i], re.IGNORECASE)
                    if match or i == len(lines):
                        if question_number is not None:
                            # Check if the last line is empty before adding a newline character
                            new_content = "\n".join(new_lines)
                            if new_content and not new_content.endswith("\n"):
                                new_content += "\n"
                            with open(
                                os.path.join(
                                    markdown_output_folder,
                                    folder,
                                    f"document_feedback_{question_number}.md",
                                ),
                                "w",
                            ) as f:
                                f.write(new_content)
                            new_lines = []
                        if match:
                            question_number = match.group(1)
                if question_number is not None:
                    new_lines.append(lines[i])
                i += 1
            # Handle the last question
            if new_lines:
                new_content = "\n".join(new_lines)
                if new_content and not new_content.endswith("\n"):
                    new_content += "\n"
                with open(
                    os.path.join(
                        markdown_output_folder,
                        folder,
                        f"document_feedback_{question_number}.md",
                    ),
                    "w",
                ) as f:
                    f.write(new_content)

            # Rename the document.md file to document_instructor.md
            os.rename(
                markdown_file,
                os.path.join(markdown_output_folder, folder, "document_instructor.md"),
            )

            # Rename the document_to_share.md file to document.md
            os.rename(
                os.path.join(markdown_output_folder, folder, "document_to_share.md"),
                markdown_file,
            )


def generate_htmls(folders):
    markdown_output_folder = config["project_markdown_output_folder"]
    html_output_folder = config["project_html_output_folder"]
    source_folder = config["project_source_folder"]

    for folder in folders:
        markdown_file = os.path.join(markdown_output_folder, folder, "document.md")
        html_folder = os.path.join(html_output_folder, folder)
        os.makedirs(html_folder, exist_ok=True)
        html_file = os.path.join(html_folder, "document.html")

        # Copy CSS file to styles folder
        styles_folder = os.path.join(html_folder, "styles")
        os.makedirs(styles_folder, exist_ok=True)
        shutil.copy(config["project_pandoc_css_file"], styles_folder)

        # Copy includes folder to HTML output folder
        includes_folder_source = os.path.join(
            markdown_output_folder, folder, "includes"
        )
        includes_folder_dest = os.path.join(html_folder, "includes")
        if os.path.exists(includes_folder_dest):
            shutil.rmtree(includes_folder_dest)
        if os.path.exists(includes_folder_source):
            shutil.copytree(includes_folder_source, includes_folder_dest)

        # Specify the metadata file
        settings_file = os.path.join(source_folder, folder, "settings.yaml")

        command = [
            "pandoc",
            markdown_file,
            "--standalone",
            "--css",
            os.path.join("styles", os.path.basename(config["project_pandoc_css_file"])),
            "--metadata-file",
            settings_file,
            "-o",
            html_file,
        ]
        subprocess.run(command)


def generate_assignment_pdfs(folders):
    markdown_output_folder = config["project_markdown_output_folder"]
    pdf_output_folder = config["project_pdf_output_folder"]
    source_folder = config["project_source_folder"]

    for folder in folders:
        folder_path = os.path.join(markdown_output_folder, folder)
        for file in os.listdir(folder_path):
            if file.endswith(".md"):
                markdown_file = os.path.join(folder_path, file)
                pdf_folder = os.path.join(pdf_output_folder, folder)
                os.makedirs(pdf_folder, exist_ok=True)
                pdf_file = os.path.join(pdf_folder, file.replace(".md", ".pdf"))
                settings_file = os.path.join(source_folder, folder, "settings.yaml")

                command = ["pandoc", markdown_file, "-o", pdf_file]
                if os.path.exists(settings_file):
                    command.extend(["--metadata-file", settings_file])
                if config.get("project_pandoc_pdf_engine"):
                    command.extend(
                        ["--pdf-engine", config["project_pandoc_pdf_engine"]]
                    )
                if config.get("project_pandoc_pdf_template"):
                    command.extend(
                        ["--template", config["project_pandoc_pdf_template"]]
                    )
                if config.get("pandoc_highlight_style"):
                    command.extend(
                        ["--highlight-style", config["pandoc_highlight_style"]]
                    )
                if config.get("project_pandoc_latex_header"):
                    command.extend(["-H", config["project_pandoc_latex_header"]])
                command.extend(
                    ["--resource-path", os.path.join(markdown_output_folder, folder)]
                )
                subprocess.run(command)


def generate_pdfs(folders):
    markdown_output_folder = config["project_markdown_output_folder"]
    pdf_output_folder = config["project_pdf_output_folder"]
    source_folder = config["project_source_folder"]

    for folder in folders:
        markdown_file = os.path.join(markdown_output_folder, folder, "document.md")
        pdf_folder = os.path.join(pdf_output_folder, folder)
        os.makedirs(pdf_folder, exist_ok=True)
        pdf_file = os.path.join(pdf_folder, "document.pdf")
        settings_file = os.path.join(source_folder, folder, "settings.yaml")

        command = ["pandoc", markdown_file, "-o", pdf_file]
        if os.path.exists(settings_file):
            command.extend(["--metadata-file", settings_file])
        if config.get("project_pandoc_pdf_engine"):
            command.extend(["--pdf-engine", config["project_pandoc_pdf_engine"]])
        if config.get("project_pandoc_pdf_template"):
            command.extend(["--template", config["project_pandoc_pdf_template"]])
        if config.get("pandoc_highlight_style"):
            command.extend(["--highlight-style", config["pandoc_highlight_style"]])
        if config.get("project_pandoc_latex_header"):
            command.extend(["-H", config["project_pandoc_latex_header"]])
        command.extend(
            ["--resource-path", os.path.join(markdown_output_folder, folder)]
        )
        subprocess.run(command)


def get_dropbox_client(access_token):
    dbx = dropbox.Dropbox(access_token)
    try:
        # Try to get account info
        dbx.users_get_current_account()
    except AuthError:
        # If an AuthError is raised, the access token is invalid or expired
        pretty_print_error(
            "The access token is invalid or expired. Please enter a new one."
        )
        access_token = input("Enter the new access token: ")
        dbx = dropbox.Dropbox(access_token)
        try:
            # Try to get account info with the new access token
            dbx.users_get_current_account()
        except AuthError:
            # If an AuthError is raised again, the new access token is also invalid or expired
            pretty_print_error(
                "The new access token is invalid or expired. Exiting the program."
            )
            sys.exit(1)
    return dbx


def get_folders_list(source_folder):
    return [
        name
        for name in os.listdir(source_folder)
        if os.path.isdir(os.path.join(source_folder, name))
    ]


def get_modified_data_folders(folders):
    build_logs_folder = config["project_build_logs_folder"]
    modified_folders = []

    for folder in folders:
        folder_log_folder = os.path.join(build_logs_folder, folder)
        timestamp_file = os.path.join(folder_log_folder, "timestamp.txt")

        if os.path.exists(timestamp_file):
            with open(timestamp_file, "r") as f:
                timestamp = float(f.read())
        else:
            modified_folders.append(folder)
            continue

        for subfolder in ["data", "data_not_tracked"]:
            source_folder = os.path.join(
                config["project_source_folder"], folder, subfolder
            )
            if os.path.exists(source_folder):
                for root, dirs, files in os.walk(source_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.getmtime(file_path) > timestamp:
                            if folder not in modified_folders:
                                modified_folders.append(folder)
                            break

    return modified_folders


def get_modified_folders(folders):
    build_logs_folder = config["project_build_logs_folder"]
    data_to_share_links_folder = config["project_data_to_share_links_folder"]
    modified_folders = []

    for folder in folders:
        folder_log_folder = os.path.join(build_logs_folder, folder)
        timestamp_file = os.path.join(folder_log_folder, "timestamp.txt")

        if os.path.exists(timestamp_file):
            with open(timestamp_file, "r") as f:
                timestamp = float(f.read())
        else:
            modified_folders.append(folder)
            continue

        source_folder = os.path.join(config["project_source_folder"], folder)
        data_to_share_links_file = os.path.join(
            data_to_share_links_folder, f"{folder}.txt"
        )

        for root, dirs, files in os.walk(source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) > timestamp:
                    if folder not in modified_folders:
                        modified_folders.append(folder)
                    break

        if (
            os.path.exists(data_to_share_links_file)
            and os.path.getmtime(data_to_share_links_file) > timestamp
        ):
            if folder not in modified_folders:
                modified_folders.append(folder)

    return modified_folders


def import_markdown_files(source):
    markdown_files = [
        os.path.join(source, f) for f in os.listdir(source) if f.endswith(".md")
    ]
    project_source_folder = config["project_source_folder"]

    # list to track the source file and the document.md file
    file_paths = []

    # loop through markdown files
    for file in markdown_files:
        # get the file name without the extesion nor the path
        file_name = os.path.splitext(os.path.basename(file))[0]

        # see if a folder with the same name exists in project_source_folder
        if os.path.isdir(os.path.join(project_source_folder, file_name)):
            pretty_print_emphasis(
                f"Folder {file_name} already exists in {project_source_folder}. Skipping...",
                True,
            )
            continue

        # create a new folder in project_source_folder with the name file_name
        new_folder_path = os.path.join(project_source_folder, file_name)
        os.makedirs(new_folder_path, exist_ok=True)

        # create the data and data_not_tracked folders at new_folder_path if they don't exist already
        os.makedirs(os.path.join(new_folder_path, "data"), exist_ok=True)
        os.makedirs(os.path.join(new_folder_path, "data_not_tracked"), exist_ok=True)

        # copy the file to the new folder and rename it to document.md
        document_md_path = os.path.join(new_folder_path, "document.md")
        shutil.copy2(file, document_md_path)

        # add the source file and the document.md file to the list
        file_paths.append((file, document_md_path))

    # loop through file_paths and then go through document.md to find the image file
    # linked in the document and copy them to an includes folder at the destination
    for file_path in file_paths:
        # get the folder name
        folder_name = os.path.basename(os.path.dirname(file_path[1]))

        # get the includes folder path
        includes_folder_path = os.path.join(
            project_source_folder, folder_name, "includes"
        )

        # create the includes folder if it doesn't exist
        os.makedirs(includes_folder_path, exist_ok=True)

        # open the document.md file
        with open(file_path[1], "r+") as f:
            content = f.read()
            matches = re.findall(r"!\[.*\]\((.*\..*)\)", content)
            for match in matches:
                # get the image file name
                image_file_name = os.path.basename(match)

                # get the source image file path
                source_image_file_path = os.path.join(
                    os.path.dirname(file_path[0]), match
                )

                # check if the source image file exists
                if os.path.isfile(source_image_file_path):
                    # get the destination image file path
                    destination_image_file_path = os.path.join(
                        includes_folder_path, image_file_name
                    )

                    # copy the image file to the destination
                    shutil.copy2(source_image_file_path, destination_image_file_path)

                    # replace the image file path in the document.md file
                    content = content.replace(
                        match, os.path.join("includes", image_file_name)
                    )

            # write the new content to the document.md file
            f.seek(0)
            f.write(content)
            f.truncate()

    # extract yaml header if present
    # extract yaml header if present
    for file_path in file_paths:
        # get the folder name
        folder_name = os.path.basename(os.path.dirname(file_path[1]))

        # replace multiple underscores or dashes in a row with one space
        title = re.sub("_+|-+", " ", folder_name)

        # default YAML content
        default_yaml = textwrap.dedent(
            f"""\
            ---
            title: "{title}"
            author: [Your name here]
            colorlinks: TRUE
            code-block-font-size: \\footnotesize
            ..."""
        )

        # open the document.md file
        with open(file_path[1], "r+") as f:
            lines = f.readlines()

            # find the start of the YAML header
            start_of_header = next(
                (i for i, line in enumerate(lines) if line.strip() == "---"), -1
            )

            # check if the file contains a YAML header
            if start_of_header != -1:
                # find the end of the YAML header
                end_of_header = next(
                    (
                        i
                        for i, line in enumerate(lines[start_of_header:])
                        if line.strip() == "..."
                    ),
                    -1,
                )

                # check if the end of the YAML header was found
                if end_of_header != -1:
                    # adjust the end of the header index to be relative to the start of the file
                    end_of_header += start_of_header

                    # extract the YAML header
                    yaml_header = "".join(lines[start_of_header : end_of_header + 1])

                    # write the YAML header to a settings.yaml file
                    with open(
                        os.path.join(os.path.dirname(file_path[1]), "settings.yaml"),
                        "w",
                    ) as settings_file:
                        settings_file.write(yaml_header)

                    # remove the YAML header and any blank lines after it from the document.md file
                    content = "".join(lines[end_of_header + 1 :]).lstrip()

                    # write the new content to the document.md file
                    f.seek(0)
                    f.write(content)
                    f.truncate()
            else:
                # write the default YAML content to a settings.yaml file
                with open(
                    os.path.join(os.path.dirname(file_path[1]), "settings.yaml"), "w"
                ) as settings_file:
                    settings_file.write(default_yaml)


def load_config(config_file_path):
    global config
    try:
        with open(config_file_path) as json_file:
            config = json.load(json_file)
    except json.JSONDecodeError:
        print("Failed to decode JSON from config file.")
        config = {}


def pretty_print(message, verbose=False):
    if verbose:
        print(f"\033[92m{message}\033[0m")  # Green text


def pretty_print_emphasis(message):
    print(f"\033[95m{message}\033[0m")  # Purple text


def pretty_print_error(message):
    print(f"\033[91m{message}\033[0m")  # Red text


def prompt_yes_no(message, default=None):
    valid_responses = {"yes": True, "y": True, "no": False, "n": False}
    default_str = (
        ", default: no" if default is None or not default else ", default: yes"
    )
    if default is not None:
        valid_responses[""] = default

    prompt = f"\033[95m{message} (yes/no{default_str}):\033[0m "  # Purple text
    while True:
        response = input(prompt).lower()
        if response in valid_responses:
            return valid_responses[response]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")


def publish_data():
    data_output_folder = config["project_data_output_folder"]
    publish_folder_data = config["publish_folder_data"]
    data_to_share_links_folder = config["project_data_to_share_links_folder"]

    if not publish_folder_data or not os.path.exists(publish_folder_data):
        return  # Do nothing if path is empty or doesn't exist

    publish_folder_data = os.path.join(
        publish_folder_data, "data"
    )  # Add "data" to the path
    os.makedirs(
        publish_folder_data, exist_ok=True
    )  # Create the directory if it doesn't exist

    for file_name in os.listdir(data_output_folder):
        if file_name.endswith((".zip", ".gz")):
            source_data_file = os.path.join(data_output_folder, file_name)
            destination_data_file = os.path.join(publish_folder_data, file_name)
            if not os.path.exists(destination_data_file) or not filecmp.cmp(
                source_data_file, destination_data_file, shallow=False
            ):
                shutil.copy2(source_data_file, destination_data_file)
                file_name_without_extension = os.path.splitext(file_name)[0]
                new_file_name = f"{file_name_without_extension}.txt"
                new_file_path = os.path.join(data_to_share_links_folder, new_file_name)
                print(
                    f"\033[95mNew data file generated, add sharable link to\033[94m {new_file_path}\033[0m"
                )


def publish_htmls():
    html_output_folder = config["project_html_output_folder"]
    publish_folder_html = config["publish_folder_html"]

    if not publish_folder_html or not os.path.exists(publish_folder_html):
        return  # Do nothing if path is empty or doesn't exist

    publish_folder_html = os.path.join(publish_folder_html, "html")
    os.makedirs(publish_folder_html, exist_ok=True)

    pandoc_css_file = config.get("project_pandoc_css_file", "")
    styles_folder = os.path.join(publish_folder_html, "styles")
    os.makedirs(styles_folder, exist_ok=True)
    shutil.copy2(pandoc_css_file, styles_folder)

    css_file_name = os.path.basename(pandoc_css_file)
    toc_contents = [
        f'<head><link rel="stylesheet" type="text/css" href="styles/{css_file_name}"></head>',
        "<h1>Table of Contents</h1>",
    ]

    document_order = config.get("document_order", [])

    folders = os.listdir(html_output_folder)
    folders.sort(
        key=lambda folder: document_order.index(folder)
        if folder in document_order
        else float("inf")
    )
    for folder_name in folders:
        source_html_folder = os.path.join(html_output_folder, folder_name)
        if os.path.isdir(source_html_folder):
            destination_html_folder = os.path.join(publish_folder_html, folder_name)
            os.makedirs(destination_html_folder, exist_ok=True)
            for file_name in os.listdir(source_html_folder):
                if file_name.endswith(".html"):
                    source_html_file = os.path.join(source_html_folder, file_name)
                    destination_html_file = os.path.join(
                        destination_html_folder, file_name
                    )
                    if not os.path.exists(destination_html_file) or not filecmp.cmp(
                        source_html_file, destination_html_file, shallow=False
                    ):
                        shutil.copy2(source_html_file, destination_html_file)
                    if file_name == "document.html":
                        toc_contents.append(
                            f'<a href="{os.path.join(folder_name, file_name)}">{folder_name}</a><br>'
                        )
            for folder in ["includes", "styles"]:
                source_folder = os.path.join(source_html_folder, folder)
                if os.path.exists(source_folder):
                    destination_folder = os.path.join(destination_html_folder, folder)
                    shutil.copytree(
                        source_folder, destination_folder, dirs_exist_ok=True
                    )

    with open(os.path.join(publish_folder_html, "index.html"), "w") as index_file:
        index_file.write("\n".join(toc_contents))


def publish_markdown():
    markdown_output_folder = config["project_markdown_output_folder"]
    publish_folder_markdown = config["publish_folder_markdown"]

    if not publish_folder_markdown or not os.path.exists(publish_folder_markdown):
        return  # Do nothing if path is empty or doesn't exist

    publish_folder_markdown = os.path.join(publish_folder_markdown, "markdown")
    os.makedirs(publish_folder_markdown, exist_ok=True)

    readme_contents = ["# Table of Contents\n"]

    document_order = config.get("document_order", [])

    folders = os.listdir(markdown_output_folder)
    folders.sort(
        key=lambda folder: document_order.index(folder)
        if folder in document_order
        else float("inf")
    )
    for folder_name in folders:
        source_markdown_folder = os.path.join(markdown_output_folder, folder_name)
        if os.path.isdir(source_markdown_folder):
            destination_markdown_folder = os.path.join(
                publish_folder_markdown, folder_name
            )
            os.makedirs(destination_markdown_folder, exist_ok=True)
            for file_name in os.listdir(source_markdown_folder):
                if file_name.endswith(".md"):
                    source_markdown_file = os.path.join(
                        source_markdown_folder, file_name
                    )
                    destination_markdown_file = os.path.join(
                        destination_markdown_folder, file_name
                    )
                    if not os.path.exists(destination_markdown_file) or not filecmp.cmp(
                        source_markdown_file, destination_markdown_file, shallow=False
                    ):
                        shutil.copy2(source_markdown_file, destination_markdown_file)
                    escaped_folder_name = folder_name.replace(
                        "_", "\_"
                    )  # Escape underscores
                    readme_contents.append(
                        f"- [{escaped_folder_name}]({os.path.join(folder_name, file_name)})"
                    )
            includes_folder = os.path.join(source_markdown_folder, "includes")
            if os.path.exists(includes_folder):
                shutil.copytree(
                    includes_folder,
                    os.path.join(destination_markdown_folder, "includes"),
                    dirs_exist_ok=True,
                )

    with open(os.path.join(publish_folder_markdown, "README.md"), "w") as readme_file:
        readme_file.write("\n".join(readme_contents))
        readme_file.write("\n")  # Add a blank line at the end


def publish_assignment_pdfs():
    pdf_output_folder = config["project_pdf_output_folder"]
    publish_folder_pdf = config["publish_folder_pdf"]

    if not publish_folder_pdf or not os.path.exists(publish_folder_pdf):
        return  # Do nothing if path is empty or doesn't exist

    publish_folder_pdf = os.path.join(
        publish_folder_pdf, "pdf"
    )  # Add "pdf" to the path
    os.makedirs(
        publish_folder_pdf, exist_ok=True
    )  # Create the directory if it doesn't exist

    for folder_name in os.listdir(pdf_output_folder):
        source_pdf_folder = os.path.join(pdf_output_folder, folder_name)
        if os.path.isdir(source_pdf_folder):
            for file_name in os.listdir(source_pdf_folder):
                if file_name.endswith(".pdf"):
                    source_pdf_file = os.path.join(source_pdf_folder, file_name)
                    new_file_name = file_name.replace("document", folder_name)
                    destination_pdf_file = os.path.join(
                        publish_folder_pdf, new_file_name
                    )
                    if not os.path.exists(destination_pdf_file) or not filecmp.cmp(
                        source_pdf_file, destination_pdf_file, shallow=False
                    ):
                        shutil.copy2(source_pdf_file, destination_pdf_file)


def publish_pdfs():
    pdf_output_folder = config["project_pdf_output_folder"]
    publish_folder_pdf = config["publish_folder_pdf"]

    if not publish_folder_pdf or not os.path.exists(publish_folder_pdf):
        return  # Do nothing if path is empty or doesn't exist

    publish_folder_pdf = os.path.join(
        publish_folder_pdf, "pdf"
    )  # Add "pdf" to the path
    os.makedirs(
        publish_folder_pdf, exist_ok=True
    )  # Create the directory if it doesn't exist

    for folder_name in os.listdir(pdf_output_folder):
        source_pdf_folder = os.path.join(pdf_output_folder, folder_name)
        if os.path.isdir(source_pdf_folder):
            for file_name in os.listdir(source_pdf_folder):
                if file_name.endswith(".pdf"):
                    source_pdf_file = os.path.join(source_pdf_folder, file_name)
                    destination_pdf_file = os.path.join(
                        publish_folder_pdf, f"{folder_name}.pdf"
                    )
                    if not os.path.exists(destination_pdf_file) or not filecmp.cmp(
                        source_pdf_file, destination_pdf_file, shallow=False
                    ):
                        shutil.copy2(source_pdf_file, destination_pdf_file)


def remove_pagebreaks(folders):
    markdown_output_folder = config["project_markdown_output_folder"]

    for folder in folders:
        markdown_file = os.path.join(markdown_output_folder, folder, "document.md")
        with open(markdown_file, "r+") as f:
            lines = f.readlines()
            f.seek(0)
            f.truncate()
            i = 0
            while i < len(lines):
                if lines[i].strip() == "\\pagebreak":
                    i += 1
                    # Skip the next line if it's blank
                    if i < len(lines) and not lines[i].strip():
                        i += 1
                else:
                    f.write(lines[i])
                    i += 1


def replace_data_download_links_in_markdown(folders):
    markdown_output_folder = config["project_markdown_output_folder"]
    data_to_share_links_folder = config["project_data_to_share_links_folder"]

    for folder in folders:
        markdown_file = os.path.join(markdown_output_folder, folder, "document.md")
        with open(markdown_file, "r+") as f:
            content = f.read()
            link_file_path = os.path.join(data_to_share_links_folder, f"{folder}.txt")
            if os.path.exists(link_file_path):
                with open(link_file_path, "r") as link_file:
                    link = link_file.read().strip()
                if "([DATA_DOWNLOAD_LINK])" in content:
                    content = content.replace("([DATA_DOWNLOAD_LINK])", f"({link})")
                elif "[DATA_DOWNLOAD_LINK]" in content:
                    # Split the link into chunks of 50 characters
                    link_parts = [link[i : i + 50] for i in range(0, len(link), 50)]
                    # Add a backslash at the end of each line, except for the last line
                    link = "\n".join(
                        [
                            f"{part}\\" if i < len(link_parts) - 1 else f"{part}"
                            for i, part in enumerate(link_parts)
                        ]
                    )
                    # Add double quotes at the start and end of the link
                    link = f'"{link}"'
                    content = content.replace("[DATA_DOWNLOAD_LINK]", link)
                f.seek(0)
                f.write(content)
                f.truncate()


def run_spellchecker(folders):
    source_folder = config["project_source_folder"]
    build_logs_folder = config["project_build_logs_folder"]

    for folder in folders:
        markdown_file = os.path.join(source_folder, folder, "document.md")
        if os.path.exists(markdown_file):
            log_folder = os.path.join(build_logs_folder, folder)
            os.makedirs(log_folder, exist_ok=True)
            log_file = os.path.join(log_folder, "spellchecker.log")
            with open(log_file, "w") as f:
                subprocess.run(
                    ["spellchecker", "--no-suggestions", markdown_file], stdout=f
                )

            # Remove ANSI color codes
            with open(log_file, "r") as f:
                lines = f.readlines()

            clean_lines = [
                re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", line) for line in lines
            ]

            with open(log_file, "w") as f:
                f.write("".join(clean_lines))


def run_markdown_link_check(folders):
    source_folder = config["project_source_folder"]
    build_logs_folder = config["project_build_logs_folder"]

    for folder in folders:
        markdown_file = os.path.join(source_folder, folder, "document.md")
        if os.path.exists(markdown_file):
            log_folder = os.path.join(build_logs_folder, folder)
            os.makedirs(log_folder, exist_ok=True)
            log_file = os.path.join(log_folder, "markdown_link_check.log")
            with open(log_file, "w") as f:
                subprocess.run(
                    ["markdown-link-check", markdown_file],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                )


def run_markdown_lint(folders):
    source_folder = config["project_source_folder"]
    build_logs_folder = config["project_build_logs_folder"]

    for folder in folders:
        markdown_file = os.path.join(source_folder, folder, "document.md")
        if os.path.exists(markdown_file):
            log_folder = os.path.join(build_logs_folder, folder)
            os.makedirs(log_folder, exist_ok=True)
            log_file = os.path.join(log_folder, "markdown_lint.log")
            with open(log_file, "w") as f:
                subprocess.run(
                    ["mdl", markdown_file],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                )


def upload_data_files_to_dropbox_and_set_shareable_links(force=False):
    project_root = config["project_root"].rstrip("/")
    publish_folder_data = os.path.join(config["publish_folder_data"], "data")
    data_to_share_links_folder = config["project_data_to_share_links_folder"]
    project_id = config["project_id"]
    access_token = os.getenv(config["dropbox_access_token_variable"])

    # give error if id is not set
    if not project_id:
        pretty_print_error("Project ID not set in config file.")
        sys.exit(1)

    dropbox_folder_name = f"{project_id}/{os.path.basename(project_root)}"

    dbx = get_dropbox_client(access_token)

    # export access_token to environment variable
    os.environ[config["dropbox_access_token_variable"]] = access_token

    # loop through the .gz and .zip files in publish_folder_data and upload to Dropbox
    file_links = []
    for file_name in os.listdir(publish_folder_data):
        if file_name.endswith((".zip", ".gz")):
            source_data_file = os.path.join(publish_folder_data, file_name)
            destination_data_file = f"/{dropbox_folder_name}/{file_name}"

            try:
                # Check if the file exists on Dropbox
                metadata = dbx.files_get_metadata(destination_data_file)
                dropbox_file_time = metadata.server_modified

                # Get the creation time of the local file
                local_file_time = datetime.fromtimestamp(
                    os.path.getmtime(source_data_file)
                )

                # Compare the modification times
                if local_file_time > dropbox_file_time or force:
                    # Local file is newer or force is True, proceed to upload
                    raise FileNotFoundError
                else:
                    # File is already up-to-date on Dropbox
                    pretty_print(f"{file_name} is already up-to-date on Dropbox.", True)
                    continue
            except (dropbox.exceptions.ApiError, FileNotFoundError):
                # If the file does not exist on Dropbox or local file is newer, upload it
                pretty_print(f"Uploading {file_name} to Dropbox...", True)
                with open(source_data_file, "rb") as f:
                    dbx.files_upload(
                        f.read(),
                        destination_data_file,
                        mode=dropbox.files.WriteMode("overwrite"),
                    )

                # Create a shareable link for the file
                try:
                    shared_link_metadata = dbx.sharing_create_shared_link_with_settings(
                        destination_data_file
                    )
                except dropbox.exceptions.ApiError as err:
                    if "shared_link_already_exists" in str(err):
                        # If the link already exists, retrieve the existing link
                        shared_links = dbx.sharing_list_shared_links(
                            path=destination_data_file
                        ).links
                        if shared_links:
                            shared_link_metadata = shared_links[0]
                        else:
                            pretty_print_error(
                                f"Failed to retrieve the existing shareable link for {file_name}"
                            )
                            continue
                    else:
                        pretty_print_error(
                            f"Failed to create a shareable link for {file_name}: {err}"
                        )
                        continue

                # Create a tuple of the file name and the shareable link and add it to the list
                file_links.append((file_name, shared_link_metadata.url))

    # loop through the file_links list and write the sharable link to the corresponding file in data_to_share_links_folder
    for file_link in file_links:
        # Regex to remove double extensions like .tar.gz or single extension
        file_name_without_extension = re.sub(
            r"(\.tar\.gz|\.tar\.bz2|\.tar\.xz|\.[^.]+)$", "", file_link[0]
        )
        new_file_name = f"{file_name_without_extension}.txt"
        file_path = os.path.join(data_to_share_links_folder, new_file_name)

        # Read the first line of the file
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                first_line = f.readline().strip()
        else:
            first_line = None

        # Write the link to the new file if it's different from the first line
        if file_link[1] != first_line:
            with open(file_path, "w") as f:
                f.write(file_link[1])
                pretty_print(
                    f"Shareable link for {file_link[0]} written to {data_to_share_links_folder}",
                    True,
                )
        else:
            pretty_print(
                f"Shareable link for {file_link[0]} already exists in {data_to_share_links_folder}",
                True,
            )


def validate_assignment_markdown(folders):
    markdown_output_folder = config["project_markdown_output_folder"]
    for folder in folders:
        markdown_file = os.path.join(markdown_output_folder, folder, "document.md")
        with open(markdown_file, "r") as f:
            lines = f.readlines()

            in_code_block = False
            headings = []
            for line in lines:
                stripped_line = line.strip().lower()
                if stripped_line.startswith("```"):
                    in_code_block = not in_code_block
                elif not in_code_block and stripped_line.startswith("#"):
                    headings.append(stripped_line)

            assignment_pattern = re.compile(r"^# ", re.IGNORECASE)
            question_pattern = re.compile(r"^#+ Question (\d+)$", re.IGNORECASE)
            marks_pattern = re.compile(r"^#+ \d+ marks?", re.IGNORECASE)
            answer_pattern = re.compile(r"^#+ Answer", re.IGNORECASE)

            if not headings or not assignment_pattern.match(headings[0]):
                return False

            seen_question = False
            seen_marks = False
            last_question_number = 0

            for heading in headings[1:]:
                question_match = question_pattern.match(heading)
                if question_match:
                    question_number = int(question_match.group(1))
                    if seen_question or question_number != last_question_number + 1:
                        pretty_print_error(
                            f"Incorrect question numbering in {markdown_file}"
                        )
                        return False
                    seen_question = True
                    last_question_number = question_number
                elif marks_pattern.match(heading) and seen_question:
                    seen_marks = True
                elif answer_pattern.match(heading) and seen_question and seen_marks:
                    seen_question = False
                    seen_marks = False


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to PDF and HTML.")
    subparsers = parser.add_subparsers(dest="command")

    # create subcommand
    create_parser = subparsers.add_parser(
        "create", help="Create a new empty project and exit."
    )
    create_parser.add_argument(
        "-p",
        "--project",
        type=str,
        required=True,
        help="The project folder to create.",
    )
    create_parser.add_argument(
        "-e",
        "--example",
        action="store_true",
        help="Include example documents in the project.",
    )
    create_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase output verbosity.",
    )

    # import subcommand
    import_parser = subparsers.add_parser(
        "import", help="Import Markdown files into an existing project."
    )
    import_parser.add_argument(
        "-m",
        "--markdown",
        type=str,
        required=True,
        help="The folder containing the Markdown documents to import.",
    )
    import_parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=True,
        help="The configuration file of the project to import into.",
    )
    import_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase output verbosity.",
    )

    # process subcommand
    process_parser = subparsers.add_parser(
        "process", help="Process the data and documents in a project."
    )
    process_parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=True,
        help="The configuration file of the project to process.",
    )
    process_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Reprocess input files even if they have been previously processed and haven't changed.",
    )
    process_parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Remove existing content from output folders.",
    )
    process_parser.add_argument(
        "-a",
        "--assignment",
        action="store_true",
        help="Process documents in 'assignment mode'.",
    )
    process_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase output verbosity.",
    )

    # dropbox subcommand
    dropbox_parser = subparsers.add_parser(
        "dropbox",
        help="Process the data and documents in a project and publish to data to Dropbox.",
    )
    dropbox_parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=True,
        help="The configuration file of the project to process.",
    )
    dropbox_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Reprocess input files even if they have been previously processed and haven't changed.",
    )
    dropbox_parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Remove existing content from output folders.",
    )
    dropbox_parser.add_argument(
        "-a",
        "--assignment",
        action="store_true",
        help="Process documents in 'assignment mode'.",
    )
    dropbox_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase output verbosity.",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if not (
        sys.version_info.major == required_major
        and sys.version_info.minor >= required_minor
    ):
        pretty_print_error(
            f"This script requires Python {required_major}.{required_minor} or higher!"
        )
        sys.exit(1)

    if hasattr(args, "config") and args.config:
        config_file_path = args.config
    else:
        config_file_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "config", "config.json"
        )

    load_config(config_file_path)

    base_dir = os.path.dirname(os.path.realpath(__file__))
    if not config.get("project_root"):
        config["project_root"] = base_dir

    for key, value in config.items():
        if isinstance(value, str) and key not in [
            "document_order",
            "pandoc_highlight_style",
            "pandoc_pdf_engine",
        ]:  # Skip keys
            config[key] = os.path.expanduser(value)

    for key, value in config.items():
        if (
            isinstance(value, str)
            and key.startswith("project_")
            and key != "project_root"
        ):
            config[key] = os.path.join(config["project_root"], value)

    for key, value in config.items():
        if isinstance(value, str) and key in [
            "project_pandoc_pdf_template",
            "project_pandoc_latex_header",
            "project_pandoc_css_file",
        ]:
            if not check_file_exists(value):
                pretty_print_error(f"File does not exist: {value}")
                sys.exit(1)

    if args.command == "create":
        create_project(args.project, args.example)
        pretty_print(f"Project '{args.project}' created.", args.verbose)
        sys.exit(0)

    for key, value in config.items():
        if isinstance(value, str) and key in [
            "project_source_folder",
            "project_data_to_share_links_folder",
            "project_markdown_output_folder",
            "project_pdf_output_folder",
            "project_html_output_folder",
            "project_data_output_folder",
            "project_build_logs_folder",
        ]:
            if not check_folder_exists(value):
                pretty_print_error(f"Folder does not exist: {value}")
                sys.exit(1)

    for key, value in config.items():
        if (
            isinstance(value, str)
            and value
            and key
            in [
                "publish_folder_pdf",
                "publish_folder_html",
                "publish_folder_data",
                "publish_folder_markdown",
            ]
        ):
            if not check_folder_exists(value):
                pretty_print_error(f"Folder does not exist: {value}")
                sys.exit(1)

    folders = get_folders_list(config["project_source_folder"])
    folders_copy = folders.copy()

    pretty_print("Checking executables...", args.verbose)
    executables = {
        "pandoc": "https://www.python.org/downloads/",
        "markdown-link-check": "https://github.com/tcort/markdown-link-check",
        "spellchecker": "https://github.com/tbroadley/spellchecker-cli",
        "mdl": "https://github.com/markdownlint/markdownlint",
    }
    check_executables(executables, args.verbose)

    if hasattr(args, "remove") and args.remove:
        pretty_print("Cleaning output folders...", args.verbose)
        clean_folder(config["project_data_output_folder"])
        clean_folder(config["project_markdown_output_folder"])
        clean_folder(config["project_html_output_folder"])
        clean_folder(config["project_pdf_output_folder"])
        clean_folder(config["project_build_logs_folder"])

    if args.command == "import":
        pretty_print("Importing Markdown files...", args.verbose)
        import_markdown_files(args.markdown)
        sys.exit(0)

    if not (hasattr(args, "force") and args.force):
        folders = get_modified_folders(folders)

    pretty_print("Copying and compressing data folders...", args.verbose)

    if hasattr(args, "force") and args.force:
        copy_and_compress_data_folders(folders)
    else:
        copy_and_compress_data_folders(get_modified_data_folders(folders))

    pretty_print("Publishing data...", args.verbose)
    publish_data()

    pretty_print("Creating link files...", args.verbose)
    create_link_files(folders)

    if args.command == "dropbox":
        if not dropbox_available:
            pretty_print_error("Dropbox is not available.")
            pretty_print_error("Install using 'pip install dropbox'.")
            sys.exit(1)

        pretty_print("Sharing data files using Dropbox...", args.verbose)
        upload_data_files_to_dropbox_and_set_shareable_links(args.force)
        # need to reprocess documents that have modified link files
        folders = get_modified_folders(folders_copy)

    pretty_print("Copying source folders to Markdown output...", args.verbose)
    copy_source_folders_to_markdown_output(folders)

    pretty_print("Editing Markdown includes...", args.verbose)
    edit_markdown_includes(folders)

    pretty_print("Running spellchecker...", args.verbose)
    run_spellchecker(folders)

    pretty_print("Running Markdown link check...", args.verbose)
    run_markdown_link_check(folders)

    pretty_print("Running Markdown lint...", args.verbose)
    run_markdown_lint(folders)

    pretty_print(
        "Replacing [DATA_DOWNLOAD_LINK] with data links in Markdown...", args.verbose
    )
    replace_data_download_links_in_markdown(folders)

    if hasattr(args, "assignment") and args.assignment:
        pretty_print("Processing documents as assignments...", args.verbose)

        pretty_print("Validating assignment Markdown...", args.verbose)
        validate_assignment_markdown(folders)

        pretty_print("Generating new Markdown...", args.verbose)
        generate_assignment_markdown(folders)

        pretty_print("Generating PDFs...", args.verbose)
        generate_assignment_pdfs(folders)

        pretty_print("Publishing PDFs...", args.verbose)
        publish_assignment_pdfs()

        pretty_print("Creating timestamp files...", args.verbose)
        create_timestamp_files(folders)

        pretty_print("🎉🎉🎉   Done.", args.verbose)

        sys.exit(0)

    pretty_print("Generating PDFs...", args.verbose)
    generate_pdfs(folders)

    pretty_print("Removing page breaks...", args.verbose)
    remove_pagebreaks(folders)

    pretty_print("Generating HTMLs...", args.verbose)
    generate_htmls(folders)

    pretty_print("Publishing PDFs...", args.verbose)
    publish_pdfs()

    pretty_print("Publishing Markdown...", args.verbose)
    publish_markdown()

    pretty_print("Publishing HTMLs...", args.verbose)
    publish_htmls()

    pretty_print("Creating timestamp files...", args.verbose)
    create_timestamp_files(folders)

    pretty_print("🎉🎉🎉   Done.", args.verbose)


if __name__ == "__main__":
    main()
