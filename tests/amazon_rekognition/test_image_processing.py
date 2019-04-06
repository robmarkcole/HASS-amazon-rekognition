"""The tests for the Amazon Rekognition component."""
from unittest.mock import Mock, mock_open, patch

import pytest
import requests
import requests_mock

from homeassistant.core import callback
from homeassistant.const import (
    ATTR_ENTITY_ID, ATTR_NAME, CONF_FRIENDLY_NAME, CONF_PASSWORD,
    CONF_USERNAME, CONF_IP_ADDRESS, CONF_PORT,
    HTTP_BAD_REQUEST, HTTP_OK, HTTP_UNAUTHORIZED, STATE_UNKNOWN)
from homeassistant.setup import async_setup_component
import homeassistant.components.image_processing as ip
import homeassistant.components.amazon_rekognition.image_processing as ar

MOCK_TARGET = 'Car'

MOCK_RESPONSE = {'Labels': [
  {'Name': 'Car',
   'Confidence': 99.025,
   'Instances': [{'BoundingBox': 'data',
     'Confidence': 99.025},
    {'BoundingBox': 'data',
     'Confidence': 97.933}],
   'Parents': [{'Name': 'Transportation'}, {'Name': 'Vehicle'}]},
]}

MOCK_NAME = 'mock_name'

# Faces data after parsing.
PARSED_RESPONSE = {'Car': 99.03}

VALID_ENTITY_ID = 'image_processing.rekognition_Car_demo_camera'
VALID_CONFIG = {
    ip.DOMAIN: {
        'platform': 'amazon_rekognition',
        ip.CONF_SOURCE: {
            ip.CONF_ENTITY_ID: 'camera.demo_camera'}
        },
    'camera': {
        'platform': 'demo'
        }
    }

def test_parse_labels():
    assert ar.parse_labels(MOCK_RESPONSE) == PARSED_RESPONSE

def test_get_label_instances():
    assert ar.get_label_instances(MOCK_RESPONSE, MOCK_TARGET) == 2