import pandas as pd
import numpy as np
import argparse
import yaml


# Argument parser -------------------------------------------------------------

parser = argparse.ArgumentParser(
    prog="BBMRI-cohort-facts"
)
parser.add_argument('--facts', help = "name of the old facts table file") # need to add pre-existing facts and sum
parser.add_argument('--filename', help = "name of the input file") 
# parser.add_argument('--biobank_id', help = "biobank ID from BBMRI-ERIC directory") 
# parser.add_argument('--collection_id', help = "collection id from BBMRI-ERIC directory") 
parser.add_argument('--out_name', help = "name of the output file", default="facts") 
parser.add_argument('--example', help = "generates an example facts table", action = 'store_true') 
args = parser.parse_args()


filename = args.filename
out_name = args.out_name
# collection_id = f"bbmri-eric:ID:IT_{args.biobank_id}:collection:{args.collection_id}"


if args.example:
    # Example facts table generation ----------------------------------------------
    age_ranges = ["Child", "Adolescent", "Adult", "Young Adult", "Middle-aged", "Aged (65-79 years)","Aged (>80 years)"]
    disease = ["urn:miriam:icd:C18", "urn:miriam:icd:C34.9"]
    sex = ["MALE", "FEMALE"]
    material_type = ["TISSUE_FROZEN", "TISSUE_PARAFFIN_EMBEDDED", "BLOOD", "DNA"]
    df = pd.DataFrame()
    df["sample_id"] = np.random.randint(100, size=3000)
    df["patient_id"] = np.random.randint(50, size=3000)
    df["sex"] = np.random.choice(sex, 3000)
    df["disease"] = np.random.choice(disease, 3000)
    df["age_range"] = np.random.choice(age_ranges, 3000)
    df["sample_type"] = np.random.choice(material_type, 3000)
    # print(df)

    res = df.groupby(["sex", "age_range", "sample_type", "disease"], observed = True)[["patient_id", "sample_id"]].nunique().reset_index()
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
    output_file = f"outputs/bbmri-cohorts-collection-EXAMPLE.xlsx"
    res.to_excel(output_file, index = False, sheet_name="eu_bbmri_eric_IT_facts")

else:
    # Import data -----------------------------------------------------------------
    data = pd.read_excel(filename)

    # Load configuration file
    with open("config.yaml", 'r') as file:
        config = yaml.safe_load(file)

    biobank_id = config.get("biobank_id")
    collection_id = config.get("collection_id")
    # collection_id = f"bbmri-eric:ID:IT_{biobank_id}:collection:{collection_id}"

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
    data['DIAGNOSIS'] = 'urn:miriam:icd:' + data['DIAGNOSIS'].astype(str)

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
    # ids = []
    # for i in range(len(res)):
    #     unique_id = f"{args.name}{i+1}" # uuid.uuid4()
    #     id = f"bbmri-eric:factID:IT:collection:{collection_id}:id:{unique_id}"
    #     ids.append(id)

    # add collection id to each line in each data set according to collections
    res["COLLECTION_ID"] = collection_id

    # add id to each line in each data set
    # res["ID"] = ids


    # arrange and rename columns according to BBMRI guide
    res = res[
        [
            # "ID",
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
        # "id",
        "collection",
        "sex",
        "age_range",
        "sample_type",
        "disease",
        "number_of_samples",
        "number_of_donors",
    ]

    res['id'] = pd.Series()
    existing_ids = []
    existing_numbers = []
    if args.facts:
        old_facts = pd.read_excel(args.facts)
        # concat with the pre-existent facts 
        old_facts = old_facts[["id",
            "collection",
            "sex",
            "age_range",
            "sample_type",
            "disease",
            "number_of_samples",
            "number_of_donors"]]
        res_merged = pd.concat([old_facts, res])
        res_merged =  res_merged.groupby(["collection",
            "sex",
            "age_range",
            "sample_type",
            "disease"]).agg({'id' :'first',
                            'collection' : 'first',
                            'sex': 'first',
                            'age_range' : 'first',
                            'sample_type' :'first',
                            'disease' :'first',
                            'number_of_samples': 'sum', 
                            'number_of_donors': 'sum'})

        id_prex = res_merged['id'].tolist()

    

        # extract id number
        existing_ids = old_facts['id'].dropna().tolist()
        existing_numbers = [int(x.split(':')[-1]) for x in existing_ids]


    else:
        res_merged = res.copy()

    # # add FACTS id
    # next_id_number = max(existing_numbers) + 1 if existing_numbers else 1
    # for i, row in res_merged.iterrows():
    #     if pd.isna(row['id']):  # se non esiste id
    #         unique_id = next_id_number
    #         new_id = f"bbmri-eric:factID:IT:collection:{collection_id}:id:{unique_id}"
    #         res_merged.at[i, 'id'] = new_id
    #         next_id_number += 1

    # # move id to first
    # cols = list(res_merged.columns)
    # cols.insert(0, cols.pop(cols.index('id')))
    # res_merged = res_merged[cols]

    # Initialize the starting number for the new unique IDs
    next_id_number = 1

    def generate_unique_id():
        global next_id_number
        while True:
            unique_id = f"{next_id_number}"
            new_id = f"bbmri-eric:factID:IT:collection:{collection_id}:id:{unique_id}"
            if new_id not in existing_ids:
                return new_id
            next_id_number += 1

    # new IDs
    for i, row in res_merged.iterrows():
        if pd.isna(row.get('id')):  # se manca
            new_id = generate_unique_id()
            res_merged.at[i, 'id'] = new_id
        existing_ids.append(new_id)  

    # ID as first column
    cols = list(res_merged.columns)
    cols.insert(0, cols.pop(cols.index('id')))
    res_merged = res_merged[cols]



    # save to file ----------------------------------------------------------------
    output_file = f"outputs/" + str(out_name) + ".xlsx"
    res_merged.to_excel(output_file, index = False, sheet_name="eu_bbmri_eric_IT_facts")
    # res.to_excel(output_file, index = False, sheet_name="eu_bbmri_eric_IT_facts")
