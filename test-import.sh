#!/usr/bin/env bash
echo "Removing existing 'sample-project-import' project"
rm -rf sample-project-import

echo "Creating new 'sample-project-import' project"
python document-builder.py create -p sample-project-import -v

echo "Importing data into 'sample-project-import' project from 'sample-import-data'"
python document-builder.py import -c sample-project-import/config/config.json -v -m sample-import-data

echo "Processing project 'sample-project-import'"
python document-builder.py process -c sample-project-import/config/config.json -v