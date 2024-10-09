# utils

import numpy as np
import pandas as pd
from dateutil import relativedelta

global material_types
global sex_types
material_types = pd.read_excel("documents/BBMRI-Cohorts_Catagories.xlsx", sheet_name="eu_bbmri_eric_material_types")
sex_types = pd.read_excel("documents/BBMRI-Cohorts_Catagories.xlsx", sheet_name="eu_bbmri_eric_sex_types")

def apply_map(value, mapping):
    for miabis_value, biobank_values in mapping.items():
        if isinstance(biobank_values, str):
            biobank_values = [biobank_values]
        if value in biobank_values:
            return miabis_value
    return value



def generate_example():
    
    age_ranges = [
        "Child",
        "Adolescent",
        "Adult",
        "Young Adult",
        "Middle-aged",
        "Aged (65-79 years)",
        "Aged (>80 years)",
    ]
    disease = ["urn:miriam:icd:C18.2", "urn:miriam:icd:C34.9"]
    sex = ["MALE", "FEMALE"]
    material_type = ["TISSUE_FROZEN", "TISSUE_PARAFFIN_EMBEDDED", "BLOOD", "DNA"]
    df = pd.DataFrame()
    df["sample_id"] = np.random.randint(100, size=3000)
    df["patient_id"] = np.random.randint(50, size=3000)
    df["sex"] = np.random.choice(sex, 3000)
    df["disease"] = np.random.choice(disease, 3000)
    df["age_range"] = np.random.choice(age_ranges, 3000)
    df["sample_type"] = np.random.choice(material_type, 3000)

    res = (
        df.groupby(["sex", "age_range", "sample_type", "disease"], observed=True)[
            ["patient_id", "sample_id"]
        ]
        .nunique()
        .reset_index()
    )
    res.rename(
        columns={"sample_id": "number_of_samples", "patient_id": "number_of_donors"}
    )

    ids = []
    for i in range(len(res)):
        unique_id = f"FACT{i+1}"
        id = f"bbmri-eric:factID:IT:collection:00525194189:id:{unique_id}"
        ids.append(id)
    res["collection_id"] = "bbmri-eric:factID:IT:collection:00525194189"
    res["id"] = ids
    cols = list(res)
    cols.insert(0, cols.pop(cols.index("id")))
    cols.insert(1, cols.pop(cols.index("collection_id")))
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
    return res.to_excel(output_file, index=False, sheet_name="eu_bbmri_eric_IT_facts")




def mapping(data, field_mappings, value_mappings, miabis):

    # if donor age is not present, compute it from birth date
    try:
        data['DONOR_AGE']
    except:
        data['DONOR_AGE'] = data.apply(lambda x: relativedelta.relativedelta(x['DIAGNOSIS_DATE'], x['BIRTH_DATE']).years, axis=1)
        
    if not miabis:
        # Field name mappings
        for miabis_field, biobank_field in field_mappings.items():
            if biobank_field in data.columns:
                data[miabis_field] = data.pop(biobank_field)

        # Value mappings
        for key, mapping in value_mappings.items():
            if key in data.columns:
                # print(data[key].apply(lambda x: apply_map(key, x, mapping)))
                data[key] = data[key].apply(lambda x: apply_map(str(x), mapping))
    else:
        data = label_mapping(data)


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
    data["DIAGNOSIS"] = "urn:miriam:icd:" + data["DIAGNOSIS"].astype(str)

    # convert to proper datatype
    data["DIAGNOSIS"] = data["DIAGNOSIS"].astype("category")
    data["SEX"] = data["SEX"].astype("category")
    data["MATERIAL_TYPE"] = data["MATERIAL_TYPE"].astype("category")
    data["AGE_RANGE"] = data["AGE_RANGE"].astype("category")
    data["PATIENT_ID"] = data["PATIENT_ID"].astype("category")
    data["SAMPLE_ID"] = data["SAMPLE_ID"].astype("category")

    return data


def label_mapping(df):
    '''mapping from MIABIS labels to directory IDs'''

    material_d = dict(zip(material_types['label'], material_types['id']))
    sex_d = dict(zip(sex_types['label'], sex_types['id']))
    df['MATERIAL_TYPE'] = df['MATERIAL_TYPE'].map(material_d)
    df['SEX'] = df['SEX'].map(sex_d)

    return df


def validation(data):
    # Ensure that all values for MATERIAL_TYPE and SEX are valid
    if not data['MATERIAL_TYPE'].isin(material_types['id']).all():
        raise ValueError("MATERIAL_TYPE values do not match the BBMRI codelist.")
    if not data['SEX'].isin(sex_types['id']).all():
        raise ValueError("SEX values do not match the BBMRI codelist.")
    