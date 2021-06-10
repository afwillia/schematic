import os
import shutil
import tempfile
import urllib.request

import connexion
from flask import current_app, request, g

from schematic import CONFIG

from schematic.utils.cli_utils import get_from_config
from schematic.manifest.generator import ManifestGenerator


# def before_request(var1, var2):
#     # Do stuff before your route executes
#     pass
# def after_request(var1, var2):
#     # Do stuff after your route executes
#     pass

# path to `config.yml` file as constant
CONFIG_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)), "config.yml"
)

# @before_request
def get_manifest_route(schema_url, title, oauth, use_annotations):
    CONFIG.load_config(CONFIG_PATH)

    # retrieve a JSON-LD via URL and store it in a temporary location
    with urllib.request.urlopen(schema_url) as response:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonld") as tmp_file:
            shutil.copyfileobj(response, tmp_file)

    # get path to temporary JSON-LD file
    jsonld = tmp_file.name

    # TODO: move schematic config parameters into FlaskApp config object
    # current_app.config['model']
    # current_app.config['input']
    # current_app.config['location']

    # request.data[]
    data_type = connexion.request.args["data_type"]

    # create object of type ManifestGenerator
    manifest_generator = ManifestGenerator(
        path_to_json_ld=jsonld,
        title=title,
        root=data_type,
        oauth=oauth,
        use_annotations=use_annotations,
    )

    dataset_id = connexion.request.args["dataset_id"]

    # call get_manifest() on manifest_generator
    result = manifest_generator.get_manifest(sheet_url=True, dataset_id=dataset_id)

    return result
