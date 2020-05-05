"""The tests for the Amazon Rekognition component."""
from .image_processing import get_object_instances, get_objects

TARGET = "person"
MOCK_HIGH_CONFIDENCE = 95.0
MOCK_LOW_CONFIDENCE = 80.0

# Mock response
MOCK_RESPONSE = {
    "Labels": [
        {
            "Name": "Human",
            "Confidence": 99.85315704345703,
            "Instances": [],
            "Parents": [],
        },
        {
            "Name": "Person",
            "Confidence": 99.85315704345703,
            "Instances": [
                {
                    "BoundingBox": {
                        "Width": 0.0759148895740509,
                        "Height": 0.5483436584472656,
                        "Left": 0.8748960494995117,
                        "Top": 0.2920868694782257,
                    },
                    "Confidence": 99.85315704345703,
                },
                {
                    "BoundingBox": {
                        "Width": 0.15320314466953278,
                        "Height": 0.515958845615387,
                        "Left": 0.22776539623737335,
                        "Top": 0.2583009898662567,
                    },
                    "Confidence": 89.78672790527344,
                },
            ],
            "Parents": [],
        },
        {
            "Name": "Bike",
            "Confidence": 99.8502426147461,
            "Instances": [],
            "Parents": [{"Name": "Vehicle"}, {"Name": "Transportation"}],
        },
        {
            "Name": "Transportation",
            "Confidence": 99.8502426147461,
            "Instances": [],
            "Parents": [],
        },
        {
            "Name": "Bicycle",
            "Confidence": 99.8502426147461,
            "Instances": [
                {
                    "BoundingBox": {
                        "Width": 0.13132628798484802,
                        "Height": 0.3868344724178314,
                        "Left": 0.22395403683185577,
                        "Top": 0.5006230473518372,
                    },
                    "Confidence": 99.8502426147461,
                }
            ],
            "Parents": [{"Name": "Vehicle"}, {"Name": "Transportation"}],
        },
        {
            "Name": "Vehicle",
            "Confidence": 99.8502426147461,
            "Instances": [],
            "Parents": [{"Name": "Transportation"}],
        },
        {
            "Name": "Automobile",
            "Confidence": 99.36394500732422,
            "Instances": [],
            "Parents": [{"Name": "Vehicle"}, {"Name": "Transportation"}],
        },
        {
            "Name": "Car",
            "Confidence": 99.36394500732422,
            "Instances": [
                {
                    "BoundingBox": {
                        "Width": 0.34410926699638367,
                        "Height": 0.47807249426841736,
                        "Left": 0.2895631790161133,
                        "Top": 0.2647375762462616,
                    },
                    "Confidence": 99.36394500732422,
                }
            ],
            "Parents": [{"Name": "Vehicle"}, {"Name": "Transportation"}],
        },
        {
            "Name": "Shoe",
            "Confidence": 97.61569213867188,
            "Instances": [
                {
                    "BoundingBox": {
                        "Width": 0.0440598800778389,
                        "Height": 0.0466512031853199,
                        "Left": 0.8933280110359192,
                        "Top": 0.7953190207481384,
                    },
                    "Confidence": 97.61569213867188,
                }
            ],
            "Parents": [{"Name": "Clothing"}, {"Name": "Footwear"}],
        },
        {
            "Name": "Cyclist",
            "Confidence": 91.20744323730469,
            "Instances": [],
            "Parents": [
                {"Name": "Bicycle"},
                {"Name": "Sport"},
                {"Name": "Vehicle"},
                {"Name": "Transportation"},
                {"Name": "Person"},
            ],
        },
        {
            "Name": "Sports",
            "Confidence": 91.20744323730469,
            "Instances": [],
            "Parents": [{"Name": "Person"}],
        },
        {
            "Name": "Road",
            "Confidence": 71.86132049560547,
            "Instances": [],
            "Parents": [],
        },
        {
            "Name": "People",
            "Confidence": 58.18419647216797,
            "Instances": [],
            "Parents": [{"Name": "Person"}],
        },
    ],
    "LabelModelVersion": "2.0",
    "ResponseMetadata": {
        "RequestId": "1bed57e8-0ce3-4c0b-8874-443567ee3354",
        "HTTPStatusCode": 200,
        "HTTPHeaders": {
            "content-type": "application/x-amz-json-1.1",
            "date": "Mon, 04 May 2020 20:11:43 GMT",
            "x-amzn-requestid": "1bed57e8-0ce3-4c0b-8874-443567ee3354",
            "content-length": "3327",
            "connection": "keep-alive",
        },
        "RetryAttempts": 0,
    },
}

PARSED_RESPONSE = {
    "bicycle": 99.9,
    "car": 99.4,
    "person": 99.9,
    "shoe": 97.6,
}


def test_get_objects():
    assert get_objects(MOCK_RESPONSE) == PARSED_RESPONSE


def test_get_object_instances():
    assert len(get_object_instances(MOCK_RESPONSE, TARGET, MOCK_HIGH_CONFIDENCE)) == 1
    assert len(get_object_instances(MOCK_RESPONSE, TARGET, MOCK_LOW_CONFIDENCE)) == 2
