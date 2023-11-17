# document-builder

The `document-builder.py` script is used to generate various documents from Markdown source files. The script uses [Pandoc](https://pandoc.org/) to convert the Markdown files to HTML and PDF files. The script also performs several other tasks, including:

* Checking the Markdown files for broken links.
* Checking the Markdown files for spelling errors.
* Checking the Markdown files for formatting errors.
* Generating a `.tar.gz` file containing data files to be shared with readers of the final documents.
* Generating a `.txt` file containing a sharable link to the `.tar.gz` file.
* Inserting the sharable link into the final documents.

## Requirements

* [Pandoc](https://pandoc.org/)
* [markdown-link-check](https://github.com/tcort/markdown-link-check)
* [spellchecker](https://github.com/tbroadley/spellchecker-cli)
* [mdl](https://github.com/markdownlint/markdownlint)

## Usage

Create a new project using the `-p` option:

```bash
python document-builder.py -p my_project
```

This will create a new folder named `my_project` containing the files and folders needed to generate the final documents.

Add content to the `my_project/source` folder, replacing the example content. Each folder in `my_project/source` corresponds to a document. Rename the folders or add new folders to hold the documents to be processed.

Each document folder in `my_project/source` should contain the following files and folders:

* `document.md` - the document in Markdown format.
* `settings.yaml` - the settings for the document in YAML format. This file is used to add title, header, and footer content to the document. See example below.
* `includes` - a folder containing any files that are to be included with or in the document. Typically this folder will contain images.
* `data` - a folder of various files to be used/consumed in conjunction with the document (for example data files to be processed using commands in the document). These files will be used to create a `.tar.gz` file named after the folder, for example `document_one.tar.gz`. Once a sharable link to this file is obtained it can be added to the `document_one.txt` file that is automatically created in the `data_to_share_links` folder. The link in `document_one.txt` will then be inserted into the derived documents, replacing any instances of `[DATA_DOWNLOAD_LINK]`, so that readers of the final documents can download the data files.
* `data_not_tracked` - additional data files and folders to be included in the `.tar.gz` file that won't be tracked by git. Generally this will be used for large files (e.g. larger than 50 MB).

To generate the final documents from the Markdown source files, run the following command:

```bash
python document-builder.py -c my_project/config/config.json
```

As new documents are added to the `source` folder, re-run the above command to generate the final documents.

Useful options for the above command include:

* `--data` - generate the data files to share and exit. This option allows you to then upload the data files to a server and obtain a sharable link to the files. The link can then be added to the `my_document.txt` file in the `data_to_share_links` folder. One these links are added, re-run `document-builder.py` without the `--data` option to generate the final documents with the shareable links inserted.
* `--force` - generate all output files even if the source files have not changed.
* `--remove` - remove all generated files and exit. This is useful if you have removed or renamed document folders and want to remove the corresponding output files.
* `--verbose` - print verbose output. This is useful for monitoring the progress of the script.

The HTML and Markdown documents copied to the publish directories will include a table of contents file with links to the individual document files. The sorting of the items in the table of contents can be controlled using the `document_order` key in the `config.json` file. The value of this key is a list of document names. The documents will be sorted in the order they appear in the list. Documents not in the list will be sorted alphabetically after the documents in the list.

Example of `settings.yaml`:

```yaml
---
title: "Tutorial: NCBI"
author: [AFNS 508 - Paul Stothard]
colorlinks: TRUE
code-block-font-size: \footnotesize
...
```
