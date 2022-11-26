from rich import print
import json
from jsonschema import validate
import os


with open('./schemas/observation_schema.json', 'r') as fd:
    schema = json.load(fd)

for f in os.scandir('./examples'):
    with open(f.path, 'r') as fd:
        print(f"[red]{f.name}[/red]", end='')
        validate(json.load(fd), schema)
        print(" :white_check_mark:")
