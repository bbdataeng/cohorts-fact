# Cohorts FACTS generator


## Requirements
``` shell
pip install pandas numpy
``` 

## Usage

If you want to generate an example FACT table:
``` shell
cohorts.py --example
``` 

If you want to generate FACT tables from your data:
``` shell
cohorts.py --filename <FILENAME> --biobank_id <BIOBANK ID> --collection_id <COLLECTION ID> --name <OUTPUT NAME>
``` 