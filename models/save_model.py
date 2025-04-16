# save_model.py
import json
import pandas as pd

class SaveModel:
    def prepare_data(self, generated_data):
        """
        Convertit la structure des données générées (DataFrame ou liste)
        en un objet Python compatible avec JSON.
        """
        if isinstance(generated_data, pd.DataFrame):
            # Mode "Sessions" : s'il y a une colonne 'actions', extraire sa liste
            if "actions" in generated_data.columns:
                return generated_data["actions"].tolist()
            else:
                return generated_data.to_dict(orient="records")
        elif isinstance(generated_data, list):
            return generated_data
        else:
            return str(generated_data)

    def save_data(self, file_name, data_to_save):
        """
        Sauvegarde l'objet 'data_to_save' dans le fichier spécifié en format JSON.
        """
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(data_to_save, file, ensure_ascii=False, indent=4)
