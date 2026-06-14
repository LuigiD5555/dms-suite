import ujson
from pathlib import Path


class JSONToolkit:
    def __init__(self):
        pass

    @staticmethod
    def get_nested_value(data: dict, **kwargs: list) -> any:
        for key in kwargs:
            data = data.get(key, None)
            if data is None:
                return None
        return data

    @staticmethod
    def import_data(data_name: str) -> dict:
        # Ensure the file extension is '.json' if not provided
        if not data_name.endswith('.json'):
            data_name = f"{data_name}.json"

        # Define the directory where the current script is located
        JSON_DIR = Path(__file__).resolve().parent
        file_path = JSON_DIR / data_name

        # Open and load the JSON file
        with open(file_path, "r") as file:
            data = ujson.load(file)

        return data

    def import_choices(self, data_name: str, return_format: str = "as_tuple") -> any:
        # Ensure the file extension is '.json' if not provided
        if not data_name.endswith('.json'):
            data_name = f"{data_name}.json"

        # Define the directory where the current script is located
        JSON_DIR = Path(__file__).resolve().parent
        file_path = JSON_DIR / data_name

        # Open and load the JSON file
        with open(file_path, "r") as file:
            data = ujson.load(file)

        # Dictionary to map return_format to the correct method
        format_mapping = {
            "as_tuple": self._import_as_tuples,
            "as_list": self._import_as_list
        }

        # Get the corresponding function based on return_format
        try:
            return_format_func = format_mapping[return_format]
        except KeyError:
            raise ValueError(f"Unknown return format: {return_format}")

        # Call the selected function
        return return_format_func(data)

    @staticmethod
    def _import_as_tuples(data: dict) -> dict:
        choices = data.get("choices", {})
        result = {key: tuple((item[0], item[1]) for item in value) for key, value in choices.items()}
        return result

    @staticmethod
    def _import_as_list(data: dict) -> dict:
        choices = data.get("choices", {})
        result = {key: [(item[0], item[1]) for item in value] for key, value in choices.items()}
        return result


# Example usage
if __name__ == "__main__":
    jtools = JSONToolkit()
    system_data = jtools.import_data("settings_variables.json")
    report_data = jtools.import_data("report_variables")
    choices_data = jtools.import_choices("choices_variables", "as_tuple")
    choices_data2 = jtools.import_choices("choices_variables", "as_list")

    country_code = system_data['locales']['mx']['country_info']['country_code']
    print(country_code)
    print(report_data)
    print(choices_data)
    print(choices_data2)
