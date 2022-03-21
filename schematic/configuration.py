import os
import yaml


class Configuration(object):
    def __init__(self):
        # path to config.yml file
        self.CONFIG_PATH = None
        # entire configuration data
        self.DATA = None

    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if value is None and "SCHEMATIC_CONFIG" in os.environ:
            self.load_config_from_env()
            value = super().__getattribute__(name)
        elif value is None and "SCHEMATIC_CONFIG" not in os.environ:
            raise AttributeError(
                "The '%s' configuration field was accessed, but it hasn't been "
                "set yet, presumably because the schematic.CONFIG.load_config() "
                "method hasn't been run yet. Alternatively, you can re-run this "
                "code with the 'SCHEMATIC_CONFIG' environment variable set to "
                "the config.yml file, which will be automatically loaded." % name
            )
        return value

    def __getitem__(self, key):
        return self.DATA[key]

    def get(self, key, default):
        try:
            value = self[key]
        except AttributeError or KeyError:
            value = default
        return value

    @staticmethod
    def load_yaml(file_path: str) -> dict:
        with open(file_path, "r") as stream:
            try:
                config_data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                return None
        return config_data

    def normalize_path(self, path):
        # Retrieve parent directory of the config to decode relative paths
        parent_dir = os.path.dirname(self.CONFIG_PATH)
        # Ensure absolute file paths
        if not os.path.isabs(path):
            path = os.path.join(parent_dir, path)
        # And lastly, normalize file paths
        return os.path.normpath(path)

    def load_config_from_env(self):
        schematic_config = os.environ["SCHEMATIC_CONFIG"]
        print(
            "Loading config YAML file specified in 'SCHEMATIC_CONFIG' "
            "environment variable: %s" % schematic_config
        )
        return self.load_config(schematic_config)

    def load_config(self, config_path=None, syn_master_file_view=None, syn_manifest_file_name=None):
        # If config_path is None, try loading from environment
        if config_path is None and "SCHEMATIC_CONFIG" in os.environ:
            return self.load_config_from_env()
        # Otherwise, raise an error
        elif config_path is None and "SCHEMATIC_CONFIG" not in os.environ:
            raise ValueError(
                "No configuration file provided to the `config_path` argument "
                "in `load_config`()`, nor was one specified in the "
                "'SCHEMATIC_CONFIG' environment variable. Quitting now..."
            )
        # Load configuration YAML file
        config_path = os.path.expanduser(config_path)
        config_path = os.path.abspath(config_path)
        self.DATA = self.load_yaml(config_path)
        self.CONFIG_PATH = config_path
        # handle user input (for API endpoints)
        if syn_master_file_view and syn_manifest_file_name: 
            self.DATA['synapse']['master_fileview'] = syn_master_file_view
            self.DATA['synapse']['manifest_filename'] = syn_manifest_file_name
        # Return self.DATA as a side-effect
        return self.DATA

    # def load_auth_from_user(self, syn_master_file_view=None, syn_master_file_name=None, use_default=False):
    #     config = {'definitions': {'synapse_config': '.synapseConfig', 'creds_path': 'credentials.json', 'token_pickle': 'token.pickle', 'service_acct_creds': 'schematic_service_account_creds.json'}, 'synapse': {'master_fileview': 'syn23643253', 'manifest_folder': 'manifests', 'manifest_filename': 'synapse_storage_manifest.csv', 'token_creds': 'syn23643259', 'service_acct_creds': 'syn25171627'}, 'manifest': {'title': 'example', 'data_type': ['Biospecimen', 'Patient']}, 'model': {'input': {'location': 'tests/data/example.model.jsonld', 'file_type': 'local'}}, 'style': {'google_manifest': {'req_bg_color': {'red': 0.9215, 'green': 0.9725, 'blue': 0.9803}, 'opt_bg_color': {'red': 1.0, 'green': 1.0, 'blue': 0.9019}, 'master_template_id': '1LYS5qE4nV9jzcYw5sXwCza25slDfRA1CIg3cs-hCdpU', 'strict_validation': True}}}
    #     #config = {'synapse': {'master_fileview': 'syn23643253', 'manifest_folder': 'manifests', 'manifest_filename': 'synapse_storage_manifest.csv', 'token_creds': 'syn23643259', 'service_acct_creds': 'syn25171627'}}
    #     if syn_master_file_view and syn_master_file_name: 
    #         config['master_file'] = syn_master_file_view
    #         config['manifest_filename'] = syn_master_file_name
    #     elif use_default: 
    #         self.DATA = config
    #     self.DATA = config
    #     return self.DATA

    @property
    def CREDS_PATH(self):
        self._CREDS_PATH = self.DATA["definitions"]["creds_path"]
        self._CREDS_PATH = self.normalize_path(self._CREDS_PATH)
        return self._CREDS_PATH

    @property
    def TOKEN_PICKLE(self):
        self._TOKEN_PICKLE = self.DATA["definitions"]["token_pickle"]
        self._TOKEN_PICKLE = self.normalize_path(self._TOKEN_PICKLE)
        return self._TOKEN_PICKLE

    @property
    def SERVICE_ACCT_CREDS(self):
        self._SERVICE_ACCT_CREDS = self.DATA["definitions"]["service_acct_creds"]
        self._SERVICE_ACCT_CREDS = self.normalize_path(self._SERVICE_ACCT_CREDS)
        return self._SERVICE_ACCT_CREDS

    @property
    def SYNAPSE_CONFIG_PATH(self):
        self._SYNAPSE_CONFIG_PATH = self.DATA["definitions"]["synapse_config"]
        self._SYNAPSE_CONFIG_PATH = self.normalize_path(self._SYNAPSE_CONFIG_PATH)
        return self._SYNAPSE_CONFIG_PATH


CONFIG = Configuration()
