"""The tests for the Amazon Rekognition component."""
from .image_processing import get_label_instances, parse_labels

MOCK_TARGET = "Car"

MOCK_RESPONSE = {
    "Labels": [
        {
            "Name": "Car",
            "Confidence": 99.025,
            "Instances": [
                {"BoundingBox": "data", "Confidence": 99.025},
                {"BoundingBox": "data", "Confidence": 97.933},
            ],
            "Parents": [{"Name": "Transportation"}, {"Name": "Vehicle"}],
        },
    ]
}

PARSED_RESPONSE = {"Car": 99.03}


def test_parse_labels():
    assert parse_labels(MOCK_RESPONSE) == PARSED_RESPONSE


def test_get_label_instances():
    assert get_label_instances(MOCK_RESPONSE, MOCK_TARGET) == 2
