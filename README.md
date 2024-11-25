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

- `out_name` [optional]: name of the output xlsx file. if None, default `facts-<COLLECTION ID>.xlsx` is returned.

## Usage

Clone the repository:
``` shell
git clone https://github.com/bbdataeng/cohorts-fact.git
``` 

First, you have to edit `config.yaml` file. Please specify Biobank ID and Collection ID (you can find them in the [BBMRI Directory](https://directory.bbmri-eric.eu)).

Then you can run the `facts.py` script.

The toolkit offers two main options depending on whether your input data already conforms to the MIABIS standard:

1. Input Data in MIABIS Standard

If your input data already follows the MIABIS standard (see [minimal-dataset-template]("documents/minimal-dataset-template.xlsx")), you can use the `--miabis` flag:


``` shell
facts.py --filename <FILENAME> --miabis 
``` 

2. Input Data Not in MIABIS Standard

If your input data is not in the MIABIS standard, you’ll need to edit the `config.yaml` file also to map your local data fields into MIABIS CDM fields. After editing the mapping configuration, run the following command:

``` shell
facts.py --filename <FILENAME> 
``` 
 

---
If you want to generate an example FACT table, run:
``` shell
facts.py --example
```

---

The result is saved into the `output` directory.