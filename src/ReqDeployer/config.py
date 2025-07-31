import yaml

def get(key: str) -> bool | int | str:
    with open("config.yaml") as file:
        cfg = yaml.safe_load(file)
    return cfg[key]