import pandas as pd
import uuid
import argparse


parser = argparse.ArgumentParser(
    prog="BBMRI-cohort-info",
    description="The script takes in input an excel file from the local biobank system and aggregates data",
    epilog="...",
)
parser.add_argument('filename') 
parser.add_argument('biobank_id') 
parser.add_argument('collection_id') 
parser.add_argument('name') 
# parser.add_argument('start_num', required=False) 
args = parser.parse_args()

COLLECTION_ID = f"bbmri-eric:ID:IT_{args.biobank_id}:collection:{args.collection_id}"

filename = args.filename

# import data
data = pd.read_excel(filename)

# replace local system’s terms for sex / disease / age_range / sample entries with the fixed term lists from the codebooks:
bins = pd.IntervalIndex.from_tuples(
    [(2, 12), (13, 17), (18, 24), (25, 44), (45, 64), (65, 79), (80, 120)],
    closed="both",
)
data["AGE_RANGE"] = pd.cut(data["Donor age"], bins)
data["AGE_RANGE"] = data["AGE_RANGE"].apply(str)

map_storagetemp = {
    "FFPE": "TISSUE_FFPE",
    "SNAP FROZEN": "TISSUE_FROZEN",
    "BLOOD": "WHOLE_BLOOD",
    "CELL": "CELL_LINES",
    "DNA": "DNA",
    "RNA": "RNA",
    "SNAP": "TISSUE_FROZEN",
    "FROZEN": "TISSUE_FROZEN",
    "FRESH FROZEN": "TISSUE_FROZEN",
    "OCT": "TISSUE_FROZEN",
    "LIQUOR" : "LIQUOR",
    "PLASMA" : "PLASMA"
}

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
data["Sample Type"] = data["Sample Type"].map(map_storagetemp)
data["AGE_RANGE"] = data["AGE_RANGE"].map(map_agerange)
data["Sex"] = data["Sex"].map(map_sex)

data["ID Sample"] = range(len(data))

# convert to proper datatype
data["Biobanca_ICD code"] = data["Biobanca_ICD code"].astype("category")
data["Sex"] = data["Sex"].astype("category")
data["Sample Type"] = data["Sample Type"].astype("category")


# aggregate and count
res = data.groupby(["Sex", "Biobanca_ICD code", "AGE_RANGE", "Sample Type"], observed = True)[["ID Patient", "ID Sample"]].nunique().reset_index()



IDS = []
for i in range(len(res)):
    unique_id = f"{args.name}{i+1}" # uuid.uuid4()
    id = f"bbmri-eric:factID:IT:collection:{args.collection_id}:id:{unique_id}"
    IDS.append(id)

# add collection id to each line in each data set according to collections
res["COLLECTION_ID"] = COLLECTION_ID

# add id to each line in each data set
res["ID"] = IDS

# arrange and rename columns
res = res[
    [
        "ID",
        "COLLECTION_ID",
        "Sex",
        "AGE_RANGE",
        "Sample Type",
        "Biobanca_ICD code",
        "ID Sample",
        "ID Patient",
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


# save to file
output_file = f"bbmri-cohorts-collection-" + str(args.name) + ".xlsx"
res.to_excel(output_file, index = False)

