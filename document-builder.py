#!/usr/bin/env python3

import argparse
import filecmp
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time


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
            pretty_print_emphasis("New compressed data file generated:")
            pretty_print_emphasis(f"{output_data_folder}.tar.gz")
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


def create_project(folder_path):
    if os.path.exists(folder_path):
        pretty_print_error(f"Folder '{folder_path}' already exists.")
        sys.exit(1)

    os.makedirs(folder_path)

    subfolders = [
        "config",
        "logs",
        "data_to_share",
        "data_to_share_links",
        "html",
        "markdown",
        "build_includes",
        "pdf",
        "source",
    ]
    for subfolder in subfolders:
        os.makedirs(os.path.join(folder_path, subfolder))

    config_file_path = os.path.join(os.path.dirname(__file__), "config", "config.json")
    if os.path.exists(config_file_path):
        shutil.copy2(config_file_path, os.path.join(folder_path, "config"))
    else:
        pretty_print_error("Config file cannot be copied.")

    with open(os.path.join(folder_path, "config", "config.json"), "r+") as f:
        content = f.read()
        content = re.sub(
            r'"project_root": ".*"', f'"project_root": "{folder_path}"', content
        )
        f.seek(0)
        f.write(content)
        f.truncate()

    for key, value in config.items():
        if isinstance(value, str) and key in [
            "project_pandoc_pdf_template",
            "project_pandoc_latex_header",
            "project_pandoc_css_file",
        ]:
            if check_file_exists(value):
                shutil.copy2(value, os.path.join(folder_path, "build_includes"))

    documents = ["document_one", "document_two", "document_three"]
    for document in documents:
        os.makedirs(os.path.join(folder_path, "source", document))

    for document in documents:
        os.makedirs(os.path.join(folder_path, "source", document, "data"))
        os.makedirs(os.path.join(folder_path, "source", document, "data_not_tracked"))
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
            f.write("author: document-builder.py\n")
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

    prompt = f"\033[94m{message} (yes/no{default_str}):\033[0m "
    while True:
        response = input(prompt).lower()
        if response in valid_responses:
            return valid_responses[response]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")


def publish_data():
    data_output_folder = config["project_data_output_folder"]
    publish_folder_data = config["publish_folder_data"]

    if not publish_folder_data or not os.path.exists(publish_folder_data):
        return  # Do nothing if path is empty or doesn't exist

    for file_name in os.listdir(data_output_folder):
        if file_name.endswith((".zip", ".gz")):
            source_data_file = os.path.join(data_output_folder, file_name)
            destination_data_file = os.path.join(publish_folder_data, file_name)
            if not os.path.exists(destination_data_file) or not filecmp.cmp(
                source_data_file, destination_data_file, shallow=False
            ):
                shutil.copy2(source_data_file, destination_data_file)


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


def publish_pdfs():
    pdf_output_folder = config["project_pdf_output_folder"]
    publish_folder_pdf = config["publish_folder_pdf"]

    if not publish_folder_pdf or not os.path.exists(publish_folder_pdf):
        return  # Do nothing if path is empty or doesn't exist

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
            if "[DATA_DOWNLOAD_LINK]" in content:
                link_file_path = os.path.join(
                    data_to_share_links_folder, f"{folder}.txt"
                )
                if os.path.exists(link_file_path):
                    with open(link_file_path, "r") as link_file:
                        link = link_file.read().strip()
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


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to PDF and HTML.")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        help="Specify the configuration file to read from.",
    )
    parser.add_argument(
        "-d",
        "--data",
        action="store_true",
        help="Generate data files to be shared and exit.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Reprocess input files even if conversion files exist in output directory.",
    )
    parser.add_argument(
        "-p",
        "--project",
        type=str,
        help="Create a new empty project in the specified folder.",
    )
    parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Remove existing content from output folders.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Display verbose messages."
    )
    args = parser.parse_args()

    if args.config:
        config_file_path = args.config
    else:
        config_file_path = os.path.join(
            os.path.dirname(__file__), "config", "config.json"
        )

    load_config(config_file_path)

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
                print(f"File does not exist: {value}")
                sys.exit(1)

    if args.project:
        create_project(args.project)
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
                print(f"Folder does not exist: {value}")
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
                print(f"Folder does not exist: {value}")
                sys.exit(1)

    folders = get_folders_list(config["project_source_folder"])

    pretty_print("Checking executables...", args.verbose)
    executables = {
        "pandoc": "https://www.python.org/downloads/",
        "markdown-link-check": "https://github.com/tcort/markdown-link-check",
        "spellchecker": "https://github.com/tbroadley/spellchecker-cli",
        "mdl": "https://github.com/markdownlint/markdownlint",
    }
    check_executables(executables, args.verbose)

    if args.remove:
        pretty_print("Cleaning output folders...", args.verbose)
        clean_folder(config["project_data_output_folder"])
        clean_folder(config["project_markdown_output_folder"])
        clean_folder(config["project_html_output_folder"])
        clean_folder(config["project_pdf_output_folder"])
        clean_folder(config["project_build_logs_folder"])

    if not args.force:
        folders = get_modified_folders(folders)

    pretty_print("Copying and compressing data folders...", args.verbose)

    if args.force:
        copy_and_compress_data_folders(folders)
    else:
        copy_and_compress_data_folders(get_modified_data_folders(folders))

    if args.data:
        pretty_print("Data files generated.", args.verbose)
        sys.exit(0)

    pretty_print("Copying source folders to markdown output...", args.verbose)
    copy_source_folders_to_markdown_output(folders)

    pretty_print("Editing markdown includes...", args.verbose)
    edit_markdown_includes(folders)

    pretty_print("Creating link files...", args.verbose)
    create_link_files(folders)

    pretty_print("Replacing data download links in markdown...", args.verbose)
    replace_data_download_links_in_markdown(folders)

    pretty_print("Generating PDFs...", args.verbose)
    generate_pdfs(folders)

    pretty_print("Removing page breaks...", args.verbose)
    remove_pagebreaks(folders)

    pretty_print("Generating HTMLs...", args.verbose)
    generate_htmls(folders)

    pretty_print("Running spellchecker...", args.verbose)
    run_spellchecker(folders)

    pretty_print("Running markdown link check...", args.verbose)
    run_markdown_link_check(folders)

    pretty_print("Running markdown lint...", args.verbose)
    run_markdown_lint(folders)

    pretty_print("Publishing PDFs...", args.verbose)
    publish_pdfs()

    pretty_print("Publishing markdown...", args.verbose)
    publish_markdown()

    pretty_print("Publishing HTMLs...", args.verbose)
    publish_htmls()

    pretty_print("Publishing data...", args.verbose)
    publish_data()

    pretty_print("Creating timestamp files...", args.verbose)
    create_timestamp_files(folders)


if __name__ == "__main__":
    main()
