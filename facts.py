import pandas as pd
import numpy as np
import argparse
import yaml
from utils import *

# Argument parser -------------------------------------------------------------

parser = argparse.ArgumentParser(prog="BBMRI-cohort-facts")
parser.add_argument(
    "--facts", help="name of the old facts table file"
)  # need to add pre-existing facts and sum
parser.add_argument("--filename", help="name of the input file")
parser.add_argument("--alias", help="alias for the subcollection")
parser.add_argument("--out_name", help="name of the output file", default="facts")
parser.add_argument(
    "--example", help="generates an example facts table", action="store_true"
)
parser.add_argument(
    "--miabis", help="if data is in MIABIS", action="store_true"
)
args = parser.parse_args()

filename = args.filename
out_name = args.out_name
miabis = args.miabis

# Example facts table generation ----------------------------------------------
if args.example:
    generate_example()

else:
    # Import data 
    data = pd.read_excel(filename)

    # Load configuration file
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    biobank_id = config.get("biobank_id")
    collection_id = config.get("collection_id")
    alias = config.get("collection_alias")

    # Mapping ---------------------------------------------------------------------

    field_mappings = config.get("field_mappings", {})
    value_mappings = config.get("value_mappings", {})

    data = mapping(data, field_mappings, value_mappings, miabis)
    
    validation(data)


    # da aggiungere controllo su campi 

    # Aggregation and count -------------------------------------------------------
    res = (
        data.groupby(["SEX", "DIAGNOSIS", "AGE_RANGE", "MATERIAL_TYPE"], observed=True)[
            ["PATIENT_ID", "SAMPLE_ID"]
        ].nunique().reset_index()
    )

    # add collection id to each line in each data set according to collections
    res["COLLECTION_ID"] = collection_id


    # arrange and rename columns according to BBMRI guide
    res = res[
        [
            "COLLECTION_ID",
            "SEX",
            "AGE_RANGE",
            "MATERIAL_TYPE",
            "DIAGNOSIS",
            "SAMPLE_ID",
            "PATIENT_ID",
        ]
    ]
    res.columns = [
        "collection",
        "sex",
        "age_range",
        "sample_type",
        "disease",
        "number_of_samples",
        "number_of_donors",
    ]

    res["id"] = pd.Series()
    existing_ids = []
    existing_numbers = []

    # if a pre-existing fact table is provided:
    if args.facts:
        old_facts = pd.read_excel(args.facts)
        # concat with the pre-existent facts
        old_facts = old_facts[ # da controllare matching colnames!!! (Attribute Names, Entity ids, XLSX)
            [
                "id",
                "collection",
                "sex",
                "age_range",
                "sample_type",
                "disease",
                "number_of_samples",
                "number_of_donors",
            ]
        ]
        res_merged = pd.concat([old_facts, res])
        res_merged = res_merged.groupby(
            ["collection", "sex", "age_range", "sample_type", "disease"]
        ).agg(
            {
                "id": "first",
                "collection": "first",
                "sex": "first",
                "age_range": "first",
                "sample_type": "first",
                "disease": "first",
                "number_of_samples": "sum",
                "number_of_donors": "sum",
            }
        )

        id_prex = res_merged["id"].tolist()
    
        # extract id number
        existing_ids = old_facts["id"].dropna().tolist()

        existing_numbers = [int(x.split(":")[-1].replace(alias, "")) for x in existing_ids]

    else:
        res_merged = res.copy()

    # Initialize the starting number for the new unique IDs
    next_id_number = 1
    def generate_unique_id():
        global next_id_number
        while True:
            unique_id = f"{alias}{next_id_number}"
            new_id = f"bbmri-eric:factID:IT:collection:{collection_id}:id:{unique_id}" # add collection alias?
            if new_id not in existing_ids:
                return new_id
            next_id_number += 1
     

    # new IDs
    for i, row in res_merged.iterrows():

        if pd.isna(row.get("id")):  # se manca
            new_id = generate_unique_id()
            res_merged.at[i, "id"] = new_id
            existing_ids.append(new_id)

    # ID as first column
    cols = list(res_merged.columns)
    cols.insert(0, cols.pop(cols.index("id")))
    res_merged = res_merged[cols]

    print(f"Generated {res_merged.shape[0]} combinations for {collection_id}, alias {alias}.")

    # save to file ----------------------------------------------------------------
    output_file = f"outputs/" + str(out_name) + ".xlsx"
    res_merged.to_excel(output_file, index=False, sheet_name="eu_bbmri_eric_IT_facts")
