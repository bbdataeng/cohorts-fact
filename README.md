# Cohorts FACTS generator

Python script for the creation of facts for the BBMRI COHORTS.

![facts-creation](https://github.com/bbdataeng/cohorts-fact/blob/BBMRIcohortguide.png)

## Requirements
``` shell
pip install pandas numpy
``` 

## Configuration

You need to edit `config.yaml` and specify:

- biobank ID

- collecion ID

and also specify the names of your columns and values.

## Input

- filename: xlsx file containing samples to be aggregated

- ex_facts [optional]: xlsx file containing existing facts in the Directory

- out_name [optional]: name of the output xlsx file. if None, default "facts.xlsx" is returned

## Usage

First, you have to edit `config.yaml` file, defining the mapping of local data into BBMRI codelist terms.
Then you can run the `cohorts.py` script.

If you want to generate an example FACT table:
``` shell
cohorts.py --example
```

If you want to generate FACT tables from your data:
``` shell
cohorts.py --filename <FILENAME> --ex_facts <FACTS FILENAME>  
``` 

if there is no existing fact table, just omit --ex_facts flag:
``` shell
cohorts.py --filename <FILENAME> 
``` 

