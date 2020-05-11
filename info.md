# Amazon Rekognition for Home Assistant
Allows you to do object detection with [Amazon Rekognition](https://aws.amazon.com/rekognition/). 

## Features 
- See how many "targets" are detected in your camera stream.
- Entity attributes containing all detected objects and their confidence.
- Possibility to save the images with bounding boxes for labels.
  - All you have to do is set a value for `save_file_folder`.
- No automatic scans to prevent accidental over-billing.
  - You can call the `image_processing.scan` service when a scan is needed.

## Pricing
As part of the [AWS Free Tier](https://aws.amazon.com/rekognition/pricing/), you can get started with Amazon Rekognition Image for free. Upon sign-up, new Amazon Rekognition customers can analyze 5,000 images per month for the first 12 months. After that price is around $1 for 1000 images.

## Configuration

After installing, make sure to add the following to your `configuration.yaml`:
```yaml
image_processing:
  - platform: amazon_rekognition
    aws_access_key_id: !secret aws_access_key
    aws_secret_access_key: !secret aws_secret_access_key
    region_name: eu-west-1 # Optional region, default is us-east-1
    save_file_folder: /config/www/amazon-rekognition/ # Optional, image storage location
    save_timestamped_file: True # Set True to save timestamped images, default False
    confidence: 90 # Optional, default is 80
    targets: # Optional target objects, default person
      - car
      - person
    source:
      - entity_id: camera.local_file
```

**Note:** For advice on getting your Amazon credentials see the [Polly docs](https://www.home-assistant.io/components/tts.amazon_polly/).

<p align="center">
<img src="https://github.com/robmarkcole/HASS-amazon-rekognition/blob/master/assets/usage.png" width="1000">
</p>