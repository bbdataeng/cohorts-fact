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

- collection alias (if any)

- the names of columns and values in the input excel (if not MIABIS)


Minimum 6 fields required:

* Sample ID
* Patient ID
* Age
* Sex
* Material Type
* Diagnosis (ICD-10 code)


## Input

- `filename`: xlsx file containing samples to be aggregated.

- `ex_facts` [optional]: xlsx file containing existing facts in the [Directory](https://directory-backend.molgenis.net/menu/advancedsearch/dataexplorer?entity=eu_bbmri_eric_facts) 

  (must be downloaded with these options:  As column names I want: `Attribute Names` As entity values I want: `Entity ids` As download type I want: `XLSX`)

- `out_name` [optional]: name of the output xlsx file. if None, default `facts.xlsx` is returned.

## Usage

First, you have to edit `config.yaml` file.
You have to specify Biobank ID and Collection ID.
Then you can run the `facts.py` script.

#### Minimal Dataset conformance (MIABIS)
If your input data already follows the MIABIS standard (see [minimal-dataset-template]("documents/minimal-dataset-template.xlsx")), you can use the `--miabis` flag for quicker conversion:


``` shell
facts.py --filename <FILENAME> --miabis 
``` 

#### No conformance with Minimal Dataset.

If your input data is not in the MIABIS standard, you’ll need to edit the mapping_config.yml file to map your local data fields into MIABIS CDM fields. After editing the mapping configuration, run the following command:

``` shell
facts.py --filename <FILENAME> 
``` 
 
### Generate an example.

If you want to generate an example FACT table, run:
``` shell
facts.py --example
```

---

The result is saved into the `output` directory.