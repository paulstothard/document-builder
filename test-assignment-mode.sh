#!/usr/bin/env bash
echo "Processing project 'sample-project-assignment'"
rm -rf sample-project-assignment/final_documents/data/*
rm -rf sample-project-assignment/final_documents/html/*
rm -rf sample-project-assignment/final_documents/markdown/*
rm -rf sample-project-assignment/final_documents/pdf/*
python document-builder.py process -c sample-project-assignment/config/config.json -a -r -v