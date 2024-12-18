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
parser.add_argument("--outdir", help="output directory", default= "outputs")
parser.add_argument("--out_name", help="name of the output file")
parser.add_argument(
    "--example", help="generates an example facts table", action="store_true"
)
parser.add_argument("--miabis", help="if data is in MIABIS", action="store_true")
parser.add_argument("--orpha", help="if diagnosis is ORPHA", action="store_true")
args = parser.parse_args()

filename = args.filename
miabis = args.miabis

bio_list = pd.read_csv("documents/eu_bbmri_eric_biobanks_2024-11-25_10_05_03.csv")[
    "Id"
].tolist()
coll_list = pd.read_csv("documents/eu_bbmri_eric_collections_2024-11-25_10_04_10.csv")[
    "Id"
].tolist()

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
    if biobank_id not in bio_list:
        raise ValueError("Biobank ID not present into BBMRI Directory. Try Again.")
    collection_id = config.get("collection_id")
    if collection_id not in coll_list:
        raise ValueError("Collection ID not present into BBMRI Directory. Try Again.")
    alias = config.get("collection_alias")

    if args.out_name:
        out_name = args.out_name
    else:
        out_name = collection_id.split(":")[-1]
    # Mapping ---------------------------------------------------------------------
    # data['SAMPLE_PRESERVATION_MODE'] = data['SAMPLE_PRESERVATION_MODE'].str.strip()
    field_mappings = config.get("field_mappings", {})
    value_mappings = config.get("value_mappings", {})


    data = mapping(data, field_mappings, value_mappings, miabis, orpha = args.orpha)
    
    validation(data)

    # da aggiungere controllo su campi

    # Aggregation and count -------------------------------------------------------
    res = (
        data.groupby(["SEX", "DIAGNOSIS", "AGE_RANGE", "MATERIAL_TYPE"], observed=True)[
            ["PATIENT_ID", "SAMPLE_ID"]
        ]
        .nunique()
        .reset_index()
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
        old_facts = old_facts[  # da controllare matching colnames!!! (Attribute Names, Entity ids, XLSX)
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

        existing_numbers = [
            int(x.split(":")[-1].replace(alias, "")) for x in existing_ids
        ]

    else:
        res_merged = res.copy()

    # Initialize the starting number for the new unique IDs
    next_id_number = 1

    def generate_unique_id():
        global next_id_number
        while True:
            unique_id = f"{alias}{next_id_number}"
            collection_id_name = alias
            sub_id = collection_id.split(":")[-1]
            new_id = f"bbmri-eric:factID:IT_{sub_id}:id:{unique_id}"  # add collection alias?
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

    print(
        f"Generated {res_merged.shape[0]} combinations for {collection_id}, alias {alias}."
    )

    # save to file ----------------------------------------------------------------
    output_file = f"{args.outdir}/facts-collection-" + str(out_name) + ".xlsx"
    res_merged.to_excel(output_file, index=False, sheet_name="eu_bbmri_eric_IT_facts")
