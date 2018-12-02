# HASS-amazon-rekognition
Faces and object detection with [Amazon Rekognition](https://aws.amazon.com/rekognition/)

## Development
* Boto3 auth already done by [Polly integration](https://github.com/home-assistant/home-assistant/blob/master/homeassistant/components/tts/amazon_polly.py)
* [Detecting image labels](https://docs.aws.amazon.com/rekognition/latest/dg/labels-detect-labels-image.html)
* [Detecting objects](https://docs.aws.amazon.com/rekognition/latest/dg/images-s3.html)
* [Amazon python examples](https://github.com/awsdocs/amazon-rekognition-developer-guide/tree/master/code_examples/python_examples/image)

### Roadmap
* Get object detection working
* Integrate with S3 buckets - we want a web front end to show processed images and results
