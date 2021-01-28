
import logging
import pytest
import pandas as pd

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_creds():
    mock_creds = {
        'sheet_service': 'mock_sheet_service',
        'drive_service': 'mock_drive_service',
        'creds': 'mock_creds'
    }
    yield mock_creds


@pytest.fixture()
def synapse_manifest():
    return pd.read_csv("tests/data/mock_manifests/synapse_manifest.csv")


@pytest.fixture()
def local_manifest():
    return pd.read_csv("tests/data/mock_manifests/local_manifest.csv")