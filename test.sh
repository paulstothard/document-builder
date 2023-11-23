#!/usr/bin/env bash
echo "Creating 'sample-project'"
rm -rf sample-project
python document-builder.py create -p sample-project -v

echo "Importing data into 'sample-project'"
python document-builder.py import -c sample-project/config/config.json -m markdown_for_import -v

echo "Processing project 'sample-project'"
python document-builder.py process -c sample-project/config/config.json -v

echo "Creating 'sample-project-assignment'"
rm -rf sample-project-assignment
python document-builder.py create -p sample-project-assignment -v

echo "Importing data into 'sample-project-assignment'"
python document-builder.py import -c sample-project-assignment/config/config.json -m markdown_assignments_for_import -v

echo "Processing project 'sample-project-assignment' using '--assignment' flag"
python document-builder.py process -c sample-project-assignment/config/config.json -a -v
