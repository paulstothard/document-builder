#!/usr/bin/env bash
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
