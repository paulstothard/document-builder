# document-builder

The `document-builder.py` script produces nicely formatted PDF and HTML documents from Markdown source files. It also performs various checks on the source files and facilitates the sharing of data files associated with the documents. It has an "assignment mode" that allows specially formatted Markdown documents to be parsed to generate assignment and assignment key PDFs.

## Requirements

* [Python 3](https://www.python.org/) version 3.8 or higher
* [Pandoc](https://pandoc.org/)
* [markdown-link-check](https://github.com/tcort/markdown-link-check)
* [spellchecker](https://github.com/tbroadley/spellchecker-cli)
* [mdl](https://github.com/markdownlint/markdownlint)

## Usage

Create a new empty project using the `create` command:

```bash
python document-builder.py create -p my_project -e
```

This will create a new folder named `my_project` containing project subfolders, a configuration file, and example content (because of the `-e` option):

```text
my_project/
├── build_includes
├── config
├── data
├── data_links
├── final_documents
├── html
├── logs
├── markdown
├── pdf
└── source
```

Simply edit the `source` folder to add content. Initially it contains input data for three sample documents:

```text
└── source
    ├── document_one
    │   ├── data
    │   ├── data_not_tracked
    │   ├── document.md
    │   ├── includes
    │   └── settings.yaml
    ├── document_three
    │   ├── data
    │   ├── data_not_tracked
    │   ├── document.md
    │   ├── includes
    │   └── settings.yaml
    └── document_two
        ├── data
        ├── data_not_tracked
        ├── document.md
        ├── includes
        └── settings.yaml
```

Rename the document folders or add new folders to hold the documents to be processed. Each document folder must contain the following files and folders, with the names as shown:

* `data` - a folder of various files to be used/consumed in conjunction with the document (for example data files to be processed using commands in the document).
* `data_not_tracked` - a folder of additional data files. Generally this will be used for large files (e.g. larger than 50 MB). The placement of these files in a separate folder allows them to be ignored in git by adding `**/data_not_tracked/` to the `.gitignore` file.
* `document.md` - the main document in Markdown format.
* `includes` - a folder containing any files that are to be included with or in the document. Typically this folder will contain images.
* `settings.yaml` - the settings for the document in YAML format. This file is used to add title, header, and footer content to the document.

With your content in place, use the `process` command to generate the final documents from the Markdown source files:

```bash
python document-builder.py process -c my_project/config/config.json
```

The final content will be written to the `my_project/final_documents` folder, into various subfolders:

* `data` - `.tar.gz` files, one for each document for which content was provided in the `data` or `data_not_tracked` folders.
* `html` - An HTML table of contents file (`index.html`) with links to each HTML document (provided in separate subfolders).
* `markdown` - A Markdown table of contents file (`README.md`) with links to each Markdown document (provided in separate subfolders).
* `pdf` - PDF documents, one per source document.

You may want the final content to be written to folders outside of the project folder (to a Dropbox folder for example). You can edit the `config.json` file to set the locations of the final content. For example, to have the final documents and data written to `~/Library/CloudStorage/Dropbox/to_share` you would edit `config.json` so that it contains the following:

* `"publish_folder_data": "~/Library/CloudStorage/Dropbox/to_share"`
* `"publish_folder_html": "~/Library/CloudStorage/Dropbox/to_share"`
* `"publish_folder_markdown": "~/Library/CloudStorage/Dropbox/to_share"`
* `"publish_folder_pdf": "~/Library/CloudStorage/Dropbox/to_share"`

Next, create the folder that will hold the final documents (if it doesn't already exist):

```bash
mkdir -p ~/Library/CloudStorage/Dropbox/to_share
```

Re-run the `process` command to generate the final documents and data files in their new locations:

```bash
python document-builder.py process -c my_project/config/config.json
```

As needed, add new documents to the project, or edit existing documents. You can also change the data provided in the `data` and `data_not_tracked` folders. Re-run the `process` command to generate the final documents with the updated content:

```bash
python document-builder.py process -c my_project/config/config.json
```

Only the new or changed documents will be processed. The final documents will be written to the same locations as before, overwriting the previous versions.

Whenever data files are changed, you may need to update the sharable links for the data files. See the section on [sharing data files](#sharing-data-files) for details. Once you have updated the sharable links, re-run the `process` command to generate the final documents with the updated links inserted:

```bash
python document-builder.py process -c my_project/config/config.json
```

## Sharing data files

If you place a `.tar.gz` file generated by `document-builder.py` in a folder that is synced to a cloud storage service (e.g. Dropbox), you can create a sharable link to the file (e.g. by right-clicking on the file in the Dropbox folder and selecting "Copy Dropbox link"). You can then add the link to the corresponding `.txt` file in the `data_to_share_links` folder. The next time you re-run `document-builder.py`, the link for accessing the `.tar.gz` file will be inserted into the appropriate document, in place of any instances of `[DATA_DOWNLOAD_LINK]` in the document.

Should you need to update the data provided with the document, you can modify the content in the `data` or `data_not_tracked` folders, and then re-run `document-builder.py` with the `--data` option. This will generate new `.tar.gz` files again for the data folders that have been updated. You can then get the new sharable links for the updated `.tar.gz` files and add them to the corresponding `.txt` files in the `data_to_share_links` folder. Re-run `document-builder.py` without the `--data` option to generate the final documents with the updated links inserted.

## Log files

The `document-builder.py` script generates log files in the `logs` folder, in a separate subfolder for each source document. The log files contain the results of spell checking, link checking, and Markdown linting. A timestamp file is included in each log folder to indicate when the document was last processed.

## Example output

The `sample-project` folder contains an example project with three sample documents. The final documents generated from the sample project are available in the `sample-project/final_documents` folder.

## Assignment mode

Assignment mode (using the `process` command with the `--assignment` option) is used to generate assignment and assignment key PDFs from specially formatted Markdown documents. The `sample-project-assignment` folder contains an example "assignment" project with three sample assignment documents. The final documents generated from the sample project are available in the `sample-project-assignment/final_documents` folder. For assignment projects several PDFs are generated for each input document: a student version of the assignment, an instructor version of the assignment (i.e. with answers), and feedback files (PDFs that provide the answer for a single question).

To make use of this mode, use the following simple structure for the Markdown documents:

```md
# Assignment 1

Content goes here, e.g. a description of the assignment.

## Question 1

### 1 mark

Question content goes here, i.e. a question.

### Answer

Answer key content goes here, i.e. the answer to the question.

## Question 2

### 2 marks

Question content goes here, i.e. a question.

### Answer

Answer key content goes here, i.e. the answer to the question.
```

Within each content section you can have standard Markdown content, for example code blocks and images.

The `# Assignment`, `## Question`, and `### Answer` headings are required for parsing. The "mark" headings are used to add the total marks to the output documents, beneath the "Assignment" heading. Failure to include the proper headings will lead to missing or incorrect output files.

The data sharing functionality works with assignment mode. Any instances of `[DATA_DOWNLOAD_LINK]` in the Markdown documents will be replaced with the sharable links for the `.tar.gz` files in the `data_to_share_links` folder.

## Example usage

### Creating a project and adding documents manually

First create a new empty project:

```bash
python document-builder.py create -p my_project -e
```

Next add `document.md` files to folders in the `my_project/source` folder. Edit the `settings.yaml` files in the document folders to add title, header, and footer content to the documents. Copy data files to the `data` and `data_not_tracked` folders as needed.

Next, generate the final documents:

```bash
python document-builder.py process -c my_project/config/config.json
```

### Creating a project and importing existing documents

First create a new empty project:

```bash
python document-builder.py create -p my_project
```

Import Markdown documents from a folder into the project:

```bash
python document-builder.py import -c my_project/config/config.json -m sample-import-data
```

Copy data files to the `data` and `data_not_tracked` folders as needed and then generate the final documents:

```bash
python document-builder.py process -c my_project/config/config.json
```
