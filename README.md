# HASS-amazon-rekognition
Faces and object detection with [Amazon Rekognition](https://aws.amazon.com/rekognition/)

**Pricing:** As part of the [AWS Free Tier](https://aws.amazon.com/rekognition/pricing/), you can get started with Amazon Rekognition Video for free. Upon sign-up, new Amazon Rekognition Video customers can analyze 1,000 minutes of Video, per month, for the first year. After that, images are about $1 per 1000 analysed. Face metadata storage is a pittance.

## Development
* Boto3 auth already done by [Polly integration](https://github.com/home-assistant/home-assistant/blob/master/homeassistant/components/tts/amazon_polly.py)
* [Detecting image labels](https://docs.aws.amazon.com/rekognition/latest/dg/labels-detect-labels-image.html)
* [Detecting objects](https://docs.aws.amazon.com/rekognition/latest/dg/images-s3.html)
* [Amazon python examples](https://github.com/awsdocs/amazon-rekognition-developer-guide/tree/master/code_examples/python_examples/image)

### Roadmap
* Get object detection working
* Integrate with S3 buckets - we want a web front end to show processed images and results. Perhaps checkout [s3album](https://github.com/toehio/s3album). Alternatively [Photoprism](https://github.com/photoprism/photoprism/wiki) supports S3 backend? [T3 looks very interesting](https://github.com/quiltdata/t4).
* Host our own [S3 with minio](https://github.com/minio/minio) -> [on a NAS](https://docs.minio.io/docs/minio-gateway-for-nas.html)
