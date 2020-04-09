# Amazon Rekognition for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

Object detection with [Amazon Rekognition](https://aws.amazon.com/rekognition/). The state of the sensor is the number of detected `target` objects in the image, and the default taret is `Person`. Note that in order to prevent accidental over-billing, the component will not scan images automatically, but requires you to call the `image_processing.scan` service. This behaviour can be changed by configuring a `scan_interval` [as described in the docs](https://www.home-assistant.io/components/image_processing#scan_interval-and-optimising-resources).

**Pricing:** As part of the [AWS Free Tier](https://aws.amazon.com/rekognition/pricing/), you can get started with Amazon Rekognition Image for free. Upon sign-up, new Amazon Rekognition customers can analyze 5,000 images per month for the first 12 months. After that price is around $1 for 1000 images.

## Component setup
For advice on getting your Amazon credentials see the [Polly docs](https://www.home-assistant.io/components/tts.amazon_polly/). The number and type of all objects discovered are listed in the sensor attributes.

Place the `custom_components` folder in your configuration directory (or add its contents to an existing custom_components folder). Add to your `configuration.yaml`:

```yaml
image_processing:
  - platform: amazon_rekognition
    aws_access_key_id: AWS_ACCESS_KEY_ID
    aws_secret_access_key: AWS_SECRET_ACCESS_KEY
    region_name: eu-west-1 # optional region, default is us-east-1
    save_file_folder: /config/www/amazon-rekognition/ # Optional image storage
    confidence: 90 # Optional, default is 80. Only used for bounding boxes atm
    target: Car # Optional target object, default Person
    source:
      - entity_id: camera.local_file
```

### Bounding box

If you set a `save_file_folder` an image will be stored with bounding boxes drawn around the objects that have own (as in, AWS returned them). The `confidence` level is used to decide what boxes should be drawn (by default this is everything above 80%).

<p align="center">
<img src="https://github.com/robmarkcole/HASS-amazon-rekognition/blob/master/development/usage.png" width="800">
</p>

<p align="center">
<img src="https://github.com/robmarkcole/HASS-amazon-rekognition/blob/master/development/card.png" width="400">
</p>

## Community guides
Here you can find community made guides, tutorials & videos about how to install/use this Amazon Rekognition integration. If you find more links let us know.
* Object Detection in Home Assistant with Amazon Rekognition [video tutorial](https://youtu.be/1G8tnhw2N_Y) and the [full article](https://peyanski.com/amazon-rekognition-in-home-assistant)

## Development
* Boto3 auth already done by [Polly integration](https://github.com/home-assistant/home-assistant/blob/master/homeassistant/components/tts/amazon_polly.py)
* [Amazon python examples](https://github.com/awsdocs/amazon-rekognition-developer-guide/tree/master/code_examples/python_examples/image)
* For tests we have the [moto library](https://github.com/spulec/moto)

### Roadmap
* Handle bounding boxes at the platform level, currently only possible on a component level
* Integrate with S3 buckets - we want a web front end to show processed images and results. Perhaps checkout [s3album](https://github.com/toehio/s3album). Alternatively [T3 looks very interesting](https://github.com/quiltdata/t4).
* Host our own [S3 with minio](https://github.com/minio/minio) -> [on a NAS](https://docs.minio.io/docs/minio-gateway-for-nas.html) -> [Synology](https://github.com/minio/minio/issues/4210)
