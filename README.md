# HASS-amazon-rekognition
People detection with [Amazon Rekognition](https://aws.amazon.com/rekognition/). The state of the sensor is the number of people detected in the image.

**Pricing:** As part of the [AWS Free Tier](https://aws.amazon.com/rekognition/pricing/), you can get started with Amazon Rekognition Image for free. Upon sign-up, new Amazon Rekognition customers can analyze 5,000 images per month for the first 12 months. After that price is around $1 for 1000 images.

## Component setup
For advice on getting your Amazon credentials see the [Polly docs](https://www.home-assistant.io/components/tts.amazon_polly/).

Add to your `configuration.yaml`:
```yaml
image_processing:
  - platform: amazon_rekognition
    aws_access_key_id: AWS_ACCESS_KEY_ID
    aws_secret_access_key: AWS_SECRET_ACCESS_KEY
    scan_interval: 20000
    source:
      - entity_id: camera.local_file
```

## Development
* Boto3 auth already done by [Polly integration](https://github.com/home-assistant/home-assistant/blob/master/homeassistant/components/tts/amazon_polly.py)
* [Detecting image labels](https://docs.aws.amazon.com/rekognition/latest/dg/labels-detect-labels-image.html)
* [Detecting objects](https://docs.aws.amazon.com/rekognition/latest/dg/images-s3.html)
* [Amazon python examples](https://github.com/awsdocs/amazon-rekognition-developer-guide/tree/master/code_examples/python_examples/image)

### Roadmap
* Integrate with S3 buckets - we want a web front end to show processed images and results. Perhaps checkout [s3album](https://github.com/toehio/s3album). Alternatively [T3 looks very interesting](https://github.com/quiltdata/t4).
* Host our own [S3 with minio](https://github.com/minio/minio) -> [on a NAS](https://docs.minio.io/docs/minio-gateway-for-nas.html) -> [Synology](https://github.com/minio/minio/issues/4210)
