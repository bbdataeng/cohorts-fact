import customtkinter as ctk
from tkinter import filedialog, messagebox, PhotoImage
import pandas as pd
from utils import mapping, label_mapping, validation
from PIL import Image

class BBMRICohortApp:
    def __init__(self, root):
        self.root = root
        self.dataset = None
        self.field_mappings = {}
        self.value_mappings = {}
        self.miabis_compliance = ctk.StringVar(value="off")
        
        self.root.title("BBMRI Cohort Facts Generator")
        self.root.iconbitmap('img/Italy_grande_str_bbmri_bianco.ico')

        # self.root.geometry = ("4000x3000")

        ## BBMRI logo
        im = Image.open('img/Italy_grande_str_bbmri_bianco.png')
      
        self.logo = ctk.CTkImage(light_image=im, 
	                            dark_image=im, size = (int(im.size[0]/2), int(im.size[1]/2)))
        ctk.CTkLabel(root, text="", image=self.logo).grid(row=0, column=0, columnspan=2, pady=10)

        ## load biobank ids and collection ids
        self.biobank_ids = pd.read_csv("documents/eu_bbmri_eric_biobanks_2024-11-25_10_05_03.csv")['Id'].tolist()
        self.collection_ids = pd.read_csv("documents/eu_bbmri_eric_collections_2024-11-25_10_04_10.csv")['Id'].tolist()

        ## entry biobank id and collection id ---------------------------------
        ctk.CTkLabel(root, text="ID Biobanca (obbligatorio):").grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.biobank_id_entry = ctk.CTkEntry(root, width=200)
        self.biobank_id_entry.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(root, text="ID Collezione (obbligatorio):").grid(row=2, column=0, padx=10, pady=5, sticky='e')
        self.collection_id_entry = ctk.CTkEntry(root, width=200)
        self.collection_id_entry.grid(row=2, column=1, padx=10, pady=5)

        ctk.CTkLabel(root, text="Alias per la Collezione (opzionale):").grid(row=3, column=0, padx=10, pady=5, sticky='e')
        self.alias_entry = ctk.CTkEntry(root, width=200)
        self.alias_entry.grid(row=3, column=1, padx=10, pady=5)

        ## validate
        self.validate_button = ctk.CTkButton(root, text="Valida e Procedi", command=self.validate_ids)
        self.validate_button.grid(row=7, column=0, columnspan=2, pady=10)
        
        
        # Codifica per diagnosi
        ctk.CTkLabel(root, text="Codifica per le Diagnosi:").grid(row=5, column=0, padx=10, pady=5, sticky='e')
        self.optionmenu_var = ctk.StringVar(value="ICD-10")
        self.optionmenu = ctk.CTkOptionMenu(root,values=["ICD-10", "ORPHA"],
                                                # command=self.optionmenu_callback,
                                                variable=self.optionmenu_var,
                                                width=200)
        self.optionmenu.grid(column=1, row=5, columnspan=2, padx=10, pady=5)

        # MIABIS compliance
        self.checkbox = ctk.CTkCheckBox(root, text='MIABIS compliant', variable=self.miabis_compliance, onvalue="on", offvalue="off",
        hover=False)

        self.checkbox.grid(column=0, row=6, columnspan=2, pady=10)
        


    ## command functions --------------------------------------------------
    def validate_ids(self):
        biobank_id = self.biobank_id_entry.get().strip()
        collection_id = self.collection_id_entry.get().strip()
        alias = self.alias_entry.get().strip()

        if not biobank_id or not collection_id:
            messagebox.showerror("Errore", "Inserisci ID Biobanca e Collezione per procedere.")
            return

        warnings = []
        if biobank_id and biobank_id not in self.biobank_ids:
            warnings.append("ID Biobanca NON presente nella Directory BBMRI.")
        if collection_id and collection_id not in self.collection_ids:
            warnings.append("ID Collezione NON presente nella Directory BBMRI.")

        if warnings:
            messagebox.showwarning("Avviso", "\n".join(warnings))
        else:
            messagebox.showinfo("Successo", "ID validati correttamente! Carica il dataset.")
            self.validate_button.configure(text="Carica Dataset", command=self.upload_dataset)

    
    def upload_dataset(self):
        filename = filedialog.askopenfilename(title="Carica Dataset", filetypes=[("Excel Files", "*.xlsx")])
        if filename:
            try:
                self.dataset = pd.read_excel(filename)
                messagebox.showinfo("Successo", "Dataset caricato correttamente!")
                self.validate_button.configure(text="Genera Facts", command=self.generate_facts)
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile leggere il file: {e}")

    def generate_facts(self):
        try:
            if self.dataset is None:
                raise ValueError("Dataset non caricato!")
            
            # Mappatura dei dati
            self.dataset = mapping(self.dataset, self.field_mappings, self.value_mappings, miabis=False)
            self.dataset = label_mapping(self.dataset)
            if self.optionmenu_var == "ICD-10":
                self.dataset["DIAGNOSIS"] = "urn:miriam:icd:" + self.dataset["DIAGNOSIS"].astype(str)
            validation(self.dataset)
            # Aggregazione e generazione facts
            res = self.dataset.groupby(["SEX", "DIAGNOSIS", "AGE_RANGE", "MATERIAL_TYPE"], observed=True)[
                ["PATIENT_ID", "SAMPLE_ID"]
            ].nunique().reset_index()

            # Creazione ID e collezione
            alias = self.alias_entry.get() or ""
            res["collection"] = self.collection_id_entry.get().strip()
            num_coll = self.collection_id_entry.get().split(":")[-1]
            res["id"] = [
                f"bbmri-eric:factID:{num_coll}:id:{alias}{i+1}"
                for i in range(len(res))
            ]

            # Esportazione facts
            res = res[["id", "collection", "SEX", "AGE_RANGE", "MATERIAL_TYPE", "DIAGNOSIS", "SAMPLE_ID", "PATIENT_ID"]]
            res.columns = ["id", "collection", "sex", "age_range", "sample_type", "disease", "number_of_samples", "number_of_donors"]

            messagebox.showinfo(message = "Scegli la cartella e il nome con cui salvare il file.")
            save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
            if save_path:
                res.to_excel(save_path, index=False)
                messagebox.showinfo("Successo", f"Generati {len(res)} facts per la collezione {num_coll} e salvati in {save_path}")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nella generazione dei facts: {e}")

    # def miabis(self):
    #     label = ctk.CTkLabel(self, text=f"MIABIS compliant: {self.miabis_compliance.get()}")
    #     label.pack()
    # def optionmenu_callback(choice):
    #    return choice

if __name__ == "__main__":
    root = ctk.CTk()
    app = BBMRICohortApp(root)
    root.mainloop()
