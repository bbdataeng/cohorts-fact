import pandas as pd
import numpy as np
import argparse
import yaml


# Argument parser -------------------------------------------------------------

parser = argparse.ArgumentParser(
    prog="BBMRI-cohort-info",
    description="The script takes in input an excel file from the local biobank system and aggregates data in FACTS",
)
parser.add_argument('--filename', help = "name of the input file") 
parser.add_argument('--biobank_id', help = "biobank ID from BBMRI-ERIC directory") 
parser.add_argument('--collection_id', help = "collection id from BBMRI-ERIC directory") 
parser.add_argument('--name', help = "name of the output file") 
parser.add_argument('--example', help = "generates an example facts table", action='store_true') 
args = parser.parse_args()

filename = args.filename
collection_id = f"bbmri-eric:ID:IT_{args.biobank_id}:collection:{args.collection_id}"


if args.example:
    # Example facts table generation ----------------------------------------------
    age_ranges = ["Child", "Adolescent", "Adult", "Young Adult", "Middle-aged", "Aged (65-79 years)","Aged (>80 years)"]
    disease = ["C18", "C34.9"]
    sex = ["MALE", "FEMALE"]
    material_type = ["TISSUE_FROZEN", "TISSUE_PARAFFIN_EMBEDDED", "BLOOD", "DNA"]
    df = pd.DataFrame()
    df["sample_id"] = np.random.randint(100, size=3000)
    df["patient_id"] = np.random.randint(50, size=3000)
    df["sex"] = np.random.choice(sex, 3000)
    df["disease"] = np.random.choice(disease, 3000)
    df["age_range"] = np.random.choice(age_ranges, 3000)
    df["sample_type"] = np.random.choice(material_type, 3000)
    print(df)

    res = df.groupby(["sex", "disease", "age_range", "sample_type"], observed = True)[["patient_id", "sample_id"]].nunique().reset_index()
    res.rename(columns={"sample_id": "number_of_samples", "patient_id": "number_of_donors"})

    ids = []
    for i in range(len(res)):
        unique_id = f"FACT{i+1}" 
        id = f"bbmri-eric:factID:IT:collection:00525194189:id:{unique_id}"
        ids.append(id)
    res["collection_id"] = "CC12345"
    res["id"] = ids
    cols = list(res)
    cols.insert(0, cols.pop(cols.index('id')))
    cols.insert(1, cols.pop(cols.index('collection_id')))
    res = res.loc[:, cols]
    output_file = f"outputs/bbmri-cohorts-collection-EXAMPLE.xlsx"
    res.to_excel(output_file, index = False)

else:
    # Import data -----------------------------------------------------------------

    data = pd.read_excel(filename)

    # Load configuration file
    with open("mapping.yaml", 'r') as file:
        config = yaml.safe_load(file)


    # Mapping ---------------------------------------------------------------------

    field_mappings = config.get("field_mappings", {})
    value_mappings = config.get("value_mappings", {})

    # Field name mappings
    for miabis_field, biobank_field in field_mappings.items():
        if biobank_field in data.columns:
            data[miabis_field] = data.pop(biobank_field)

    # Value mappings
    def apply_map(value, mapping):
        for miabis_value, biobank_values in mapping.items():

            if isinstance(biobank_values, str):
                biobank_values = [biobank_values]
            if value in biobank_values:
                return miabis_value
        return value

    for key, mapping in value_mappings.items():
        if key in data.columns:
            # print(data[key].apply(lambda x: apply_map(key, x, mapping)))
            data[key] = data[key].apply(lambda x: apply_map(str(x), mapping))



    # replace local system’s terms for sex / disease / age_range / sample entries with the fixed term lists from the codebooks:
    bins = pd.IntervalIndex.from_tuples(
        [(2, 12), (13, 17), (18, 24), (25, 44), (45, 64), (65, 79), (80, 120)],
        closed="both",
    )
    data["AGE_RANGE"] = pd.cut(data["DONOR_AGE"], bins)
    data["AGE_RANGE"] = data["AGE_RANGE"].apply(str)


    map_agerange = {
        "[2, 12]": "Child",
        "[13, 17]": "Adolescent",
        "[18, 24]": "Young Adult",
        "[25, 44]": "Adult",
        "[45, 64]": "Middle-aged",
        "[65, 79]": "Aged (65-79 years)",
        "[80, 120]": "Aged (>80 years)",
    }

    map_sex = {"M": "Male", "F": "Female"}
    data["AGE_RANGE"] = data["AGE_RANGE"].map(map_agerange)
    # data["SEX"] = data["SEX"].map(map_sex)
    # data["SAMPLE_ID"] = range(len(data))

    # convert to proper datatype
    data["DIAGNOSIS"] = data["DIAGNOSIS"].astype("category")
    data["SEX"] = data["SEX"].astype("category")
    data["MATERIAL_TYPE"] = data["MATERIAL_TYPE"].astype("category")
    data["AGE_RANGE"] = data["AGE_RANGE"].astype("category")
    data["PATIENT_ID"] = data["PATIENT_ID"].astype("category")
    data["SAMPLE_ID"] = data["SAMPLE_ID"].astype("category")


    # Aggregation and count -------------------------------------------------------
    res = data.groupby(["SEX", "DIAGNOSIS", "AGE_RANGE", "MATERIAL_TYPE"], observed = True)[["PATIENT_ID", "SAMPLE_ID"]].nunique().reset_index()

    # create an unique ID for each row (fact) - given by args.name + int
    ids = []
    for i in range(len(res)):
        unique_id = f"{args.name}{i+1}" # uuid.uuid4()
        id = f"bbmri-eric:factID:IT:collection:{collection_id}:id:{unique_id}"
        ids.append(id)

    # add collection id to each line in each data set according to collections
    res["COLLECTION_ID"] = collection_id

    # add id to each line in each data set
    res["ID"] = ids


    # arrange and rename columns according to BBMRI guide
    res = res[
        [
            "ID",
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
        "id",
        "collection",
        "sex",
        "age_range",
        "sample_type",
        "disease",
        "number_of_samples",
        "number_of_donors",
    ]


    # save to file ----------------------------------------------------------------
    output_file = f"outputs/bbmri-cohorts-collection-" + str(args.name) + ".xlsx"
    res.to_excel(output_file, index = False)

