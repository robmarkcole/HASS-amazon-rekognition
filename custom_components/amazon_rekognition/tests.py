"""The tests for the Amazon Rekognition component."""
from .image_processing import get_object_instances, parse_labels

MOCK_TARGET = "Car"
MOCK_HIGH_CONFIDENCE = 80.0
MOCK_LOW_CONFIDENCE = 60.0

# Mock response with 2 cars
MOCK_RESPONSE = {
    "Labels": [
        {
            "Name": "Car",
            "Confidence": 99.025,
            "Instances": [
                {"BoundingBox": "data", "Confidence": 99.025},
                {"BoundingBox": "data", "Confidence": 67.933},
            ],
            "Parents": [{"Name": "Transportation"}, {"Name": "Vehicle"}],
        },
    ]
}

PARSED_RESPONSE = {"car": 99.0}


def test_parse_labels():
    assert parse_labels(MOCK_RESPONSE) == PARSED_RESPONSE


def test_get_object_instances():
    assert get_object_instances(MOCK_RESPONSE, MOCK_TARGET, MOCK_HIGH_CONFIDENCE) == 1
    assert get_object_instances(MOCK_RESPONSE, MOCK_TARGET, MOCK_LOW_CONFIDENCE) == 2
