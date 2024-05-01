#!/usr/bin/env bash

# To create a virtual environment in the project root, run the following commands:
# python -m venv venv
# source venv/bin/activate
# pip install dropbox

# Define the path to the virtual environment relative to the script
VENV_PATH="./venv"

# Check if the virtual environment exists
if [ -d "$VENV_PATH" ]; then
    echo "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
else
    echo "Virtual environment not found. Using system Python."
fi

printf "Creating 'sample-project'\n"
rm -rf sample-project
python3 document-builder.py create -p sample-project -v

printf "Importing data into 'sample-project'\n"
python3 document-builder.py import -c sample-project/config/config.json -m markdown_for_import -v

printf "Copying data files into 'sample-project'\n"
cp -r markdown_for_import/another_document_data/* sample-project/source/another_document/data/
cp -r markdown_for_import/hpc_tutorial_data/* sample-project/source/hpc_tutorial/data/

printf "Processing project 'sample-project'\n"
python3 document-builder.py process -c sample-project/config/config.json -v

printf "Updating 'sample-project'\n"
python3 document-builder.py process -c sample-project/config/config.json -v

printf "Creating 'sample-project-assignment'\n"
rm -rf sample-project-assignment
python3 document-builder.py create -p sample-project-assignment -v

printf "Importing data into 'sample-project-assignment'\n"
python3 document-builder.py import -c sample-project-assignment/config/config.json -m markdown_assignments_for_import -v

printf "Copying data into 'sample-project-assignment'\n"
cp -r markdown_assignments_for_import/assignment_1_data/* sample-project-assignment/source/assignment_1/data/
cp -r markdown_assignments_for_import/assignment_2_data/* sample-project-assignment/source/assignment_2/data/
cp -r markdown_assignments_for_import/assignment_3_data/* sample-project-assignment/source/assignment_3/data/

printf "Processing project 'sample-project-assignment' using '--assignment' flag\n"
python3 document-builder.py process -c sample-project-assignment/config/config.json -a -v

printf "Updating 'sample-project-assignment' using '--assignment' flag\n"
python3 document-builder.py process -c sample-project-assignment/config/config.json -a -v

# Deactivate virtual environment if it was activated
if [ -d "$VENV_PATH" ]; then
    deactivate
fi