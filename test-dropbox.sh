#!/usr/bin/env bash
echo "Creating 'sample-project'"
rm -rf sample-project
python document-builder.py create -p sample-project -v

echo "Importing data into 'sample-project'"
python document-builder.py import -c sample-project/config/config.json -m markdown_for_import -v

echo "Copying data files into 'sample-project'"
cp -r markdown_for_import/another_document_data/* sample-project/source/another_document/data/
cp -r markdown_for_import/hpc_tutorial_data/* sample-project/source/hpc_tutorial/data/

echo "Processing project 'sample-project'"
python document-builder.py dropbox -c sample-project/config/config.json -v

echo "Updating 'sample-project'"
python document-builder.py dropbox -c sample-project/config/config.json -v

echo "Creating 'sample-project-assignment'"
rm -rf sample-project-assignment
python document-builder.py create -p sample-project-assignment -v

echo "Importing data into 'sample-project-assignment'"
python document-builder.py import -c sample-project-assignment/config/config.json -m markdown_assignments_for_import -v

echo "Copying data into 'sample-project-assignment'"
cp -r markdown_assignments_for_import/assignment_1_data/* sample-project-assignment/source/assignment_1/data/
cp -r markdown_assignments_for_import/assignment_2_data/* sample-project-assignment/source/assignment_2/data/
cp -r markdown_assignments_for_import/assignment_3_data/* sample-project-assignment/source/assignment_3/data/

echo "Processing project 'sample-project-assignment' using '--assignment' flag"
python document-builder.py dropbox -c sample-project-assignment/config/config.json -a -v

echo "Updating 'sample-project-assignment' using '--assignment' flag"
python document-builder.py dropbox -c sample-project-assignment/config/config.json -a -v
