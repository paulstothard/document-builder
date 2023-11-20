#!/usr/bin/env bash

# remove existing sample-project-import
echo "Removing existing sample-project-import"
rm -rf sample-project-import

# create new project to import into
echo "Creating new project to import into"
python document-builder.py create -p sample-project-import -v

# import data into project
echo "Importing data into project from sample-import-data"
python document-builder.py import -c sample-project-import/config/config.json -v -m sample-import-data

# process the project as usual
echo "Processing project"
python document-builder.py process -c sample-project-import/config/config.json -v