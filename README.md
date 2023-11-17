# Tutorials

This repository is used to store tutorials in Markdown format and associated code to convert them into Markdown, PDF and HTML formats.

## Requirements

* [Pandoc](https://pandoc.org/)
* [markdown-link-check](https://github.com/tcort/markdown-link-check)
* [spellchecker](https://github.com/tbroadley/spellchecker-cli)
* [mdl](https://github.com/markdownlint/markdownlint)

## Usage

Edit the configuration file `config/config.json`, specifying the desired locations of the final output files, using the `publish_folder_*` keys.

Add documents to the `source` folder. Each new document must be added to a separate folder within the `source` folder. The name of the folder will be used as the name of files created for or derived from the document. The folder, for example `my_document`, must contain the following files and folders:

* `document.md` - the document in Markdown format.
* `settings.yaml` - the settings for the document in YAML format. These are used to add title, header, and footer content to documents. See example below.
* `includes` - a folder containing any files that are to be included with or in the document. Typically this folder will contain images.
* `data` - a folder of various files to be used/consumed in conjunction with the document (for example data files to be processed using commands in the document). These files will be used to create a `.tar.gz` file named after the folder, for example `my_document.tar.gz`. Once a sharable link to this file is obtained it can be added to the `my_document.txt` file that is automatically created in the `data_to_share_links` folder. The link in `my_document.txt` will then be inserted into the derived documents, replacing any instances of `[DATA_DOWNLOAD_LINK]`, so that readers of the final documents can download the data files.
* `data_not_tracked` - additional data files and folders to be included in the `.tar.gz` file that won't be tracked by git. Generally this will be used for large files (e.g. larger than 50 MB).

To generate the final documents from the Markdown source files, run the following command:

```bash
python publish.py -v
```

As new documents are added to the `source` folder, re-run the above command to generate the final documents.

Useful options for the above command include:

* `--data` - generate the data files to share and exit. This option allows you to then upload the data files to a server and obtain a sharable link to the files. The link can then be added to the `my_document.txt` file in the `data_to_share_links` folder. One these links are added, re-run `publish.py` without the `--data` option to generate the final documents.
* `--remove` - remove all generated files and exit. This is useful if you want to start over with a clean slate.
* `--force` - generate all output files even if the source files have not changed. This is useful if there is missing output files or if you want to update all output files. The script uses timestamps to determine if a source file has changed. These timestamps are stored in the `logs` folder.
* `--verbose` - print verbose output.

Note that the HTML and Markdown documents copied to the publish directories will include a table of contents file with links to the individual document files. The sorting of the items in the table of contents can be controlled using the `document_order` key in the `config.json` file. The value of this key is a list of document names. The documents will be sorted in the order they appear in the list. Documents not in the list will be sorted alphabetically after the documents in the list.

Example of `settings.yaml`:

```yaml
---
title: "Tutorial: NCBI"
author: [AFNS 508 - Paul Stothard]
colorlinks: TRUE
code-block-font-size: \footnotesize
...
```
