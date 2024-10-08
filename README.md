# Cohorts FACTS generator

Python script for the creation of facts for the BBMRI COHORTS.

![facts-creation](https://github.com/bbdataeng/cohorts-fact/blob/main/BBMRIcohortguide.png)

## Requirements
``` shell
pip install pandas numpy
``` 

## Configuration

You need to edit `config.yaml` and specify:

- biobank ID

- collection ID

- collection alias

- the names of columns and values in the input excel

> Minimum 6 fields required:
>  * Sample ID
>  * Patient ID
>  * Age
>  * Sex
>  * Material Type
>  * Diagnosis (ICD-10 code)

## Input

- `filename`: xlsx file containing samples to be aggregated.

- `ex_facts` [optional]: xlsx file containing existing facts in the [Directory](https://directory-backend.molgenis.net/menu/advancedsearch/dataexplorer?entity=eu_bbmri_eric_facts) 

                        (must be downloaded with these options: 
                        
                        As column names I want: Attribute Names

                        As entity values I want: Entity ids

                        As download type I want: XLSX)


- `out_name` [optional]: name of the output xlsx file. if None, default `facts.xlsx` is returned.

## Usage

First, you have to edit `config.yaml` file, defining the mapping of local data into BBMRI codelist terms.
Then you can run the `facts.py` script.

If you want to generate an example FACT table:
``` shell
facts.py --example
```

If you want to generate FACT tables from your data:
``` shell
facts.py --filename <FILENAME> --ex_facts <FACTS FILENAME>  
``` 

if there is no existing fact table, just omit --ex_facts flag:
``` shell
facts.py --filename <FILENAME> 
``` 

