# tools_model.py
import json
import os


class ToolsModel:
    MAX_PARAMS = 100
    def __init__(self, params_file="params.json"):
        self.params_file = params_file
        self.saved_params = {}
        self.load_saved_parameters()

    def load_saved_parameters(self):
        if os.path.exists(self.params_file):
            with open(self.params_file, "r") as file:
                try:
                    self.saved_params = json.load(file)
                except json.JSONDecodeError:
                    self.saved_params = {}
        else:
            self.saved_params = {}
        return self.saved_params

    def save_to_file(self):
        with open(self.params_file, "w") as file:
            json.dump(self.saved_params, file, indent=4)

    def save_parameters(self, name, params):
        if len(self.saved_params) >= ToolsModel.MAX_PARAMS:
            raise Exception("Maximum number of saved parameters reached. Please delete one before saving a new one.")
        self.saved_params[name] = params
        self.save_to_file()

    def delete_parameter(self, name):
        if name in self.saved_params:
            del self.saved_params[name]
            self.save_to_file()
            return True
        return False

    def get_parameter(self, name):
        return self.saved_params.get(name, None)

    def get_all_parameter_sets(self):
        return self.saved_params

    def get_parameter(self, name):
        return self.saved_params.get(name, None)