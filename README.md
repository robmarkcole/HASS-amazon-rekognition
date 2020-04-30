# Amazon Rekognition for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

Object detection with [Amazon Rekognition](https://aws.amazon.com/rekognition/). The state of the sensor is the number of detected `target` objects in the image, and the default target is `Person`. Note that in order to prevent accidental over-billing, the component will not scan images automatically, but requires you to call the `image_processing.scan` service.

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
    save_timestamped_file: True # Set True to save timestamped images, default False
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

## Development
* `python3 -m venv venv`
* `source venv/bin/activate`
* `pip install -r requirements-dev.txt`
* `venv/bin/py.test custom_components/amazon_rekognition/tests.py -vv -p no:warnings`