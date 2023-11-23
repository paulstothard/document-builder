#!/usr/bin/env bash
echo "Processing project 'sample-project'"
rm -rf sample-project/final_documents/data/*
rm -rf sample-project/final_documents/html/*
rm -rf sample-project/final_documents/markdown/*
rm -rf sample-project/final_documents/pdf/*
python document-builder.py process -c sample-project/config/config.json -r -v