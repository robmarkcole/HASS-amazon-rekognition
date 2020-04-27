"""
Platform that will perform object detection.
"""
import io
import logging
import re
from pathlib import Path

from PIL import Image, ImageDraw, UnidentifiedImageError

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.components.image_processing import (
    ATTR_CONFIDENCE,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_SOURCE,
    PLATFORM_SCHEMA,
    ImageProcessingEntity,
)
from homeassistant.core import split_entity_id
from homeassistant.util.pil import draw_box

_LOGGER = logging.getLogger(__name__)

CONF_REGION = "region_name"
CONF_ACCESS_KEY_ID = "aws_access_key_id"
CONF_SECRET_ACCESS_KEY = "aws_secret_access_key"

DEFAULT_REGION = "us-east-1"
SUPPORTED_REGIONS = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "ca-central-1",
    "eu-west-1",
    "eu-central-1",
    "eu-west-2",
    "eu-west-3",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-2",
    "ap-northeast-1",
    "ap-south-1",
    "sa-east-1",
]

CONF_SAVE_FILE_FOLDER = "save_file_folder"
CONF_TARGET = "target"
DEFAULT_TARGET = "Person"

CONF_SAVE_TIMESTAMPTED_FILE = "save_timestamped_file"
DATETIME_FORMAT = "%Y-%m-%d_%H:%M:%S"


REQUIREMENTS = ["boto3 == 1.9.69"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(SUPPORTED_REGIONS),
        vol.Required(CONF_ACCESS_KEY_ID): cv.string,
        vol.Required(CONF_SECRET_ACCESS_KEY): cv.string,
        vol.Optional(CONF_TARGET, default=DEFAULT_TARGET): cv.string,
        vol.Optional(CONF_SAVE_FILE_FOLDER): cv.isdir,
        vol.Optional(CONF_SAVE_TIMESTAMPTED_FILE, default=False): cv.boolean,
    }
)


def get_label_instances(response, target):
    """Get the number of instances of a target label."""
    for label in response["Labels"]:
        if (
            label["Name"].lower() == target.lower()
        ):  # Lowercase both to prevent any comparing issues
            return len(label["Instances"])
    return 0


def parse_labels(response):
    """Parse the API labels data, returning objects only."""
    return {
        label["Name"]: round(label["Confidence"], 2) for label in response["Labels"]
    }


def get_valid_filename(name):
    return re.sub(r"(?u)[^-\w.]", "", str(name).strip().replace(" ", "_"))


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up Rekognition."""

    import boto3

    aws_config = {
        CONF_REGION: config[CONF_REGION],
        CONF_ACCESS_KEY_ID: config[CONF_ACCESS_KEY_ID],
        CONF_SECRET_ACCESS_KEY: config[CONF_SECRET_ACCESS_KEY],
    }

    client = boto3.client("rekognition", **aws_config)

    save_file_folder = config[CONF_SAVE_FILE_FOLDER]
    if save_file_folder:
        save_file_folder = Path(save_file_folder)

    entities = []
    for camera in config[CONF_SOURCE]:
        entities.append(
            Rekognition(
                client,
                config[CONF_REGION],
                config[CONF_TARGET],
                config[ATTR_CONFIDENCE],
                save_file_folder,
                config[CONF_SAVE_TIMESTAMPTED_FILE],
                camera[CONF_ENTITY_ID],
                camera.get(CONF_NAME),
            )
        )
    add_devices(entities)


class Rekognition(ImageProcessingEntity):
    """Perform object and label recognition."""

    def __init__(
        self,
        client,
        region,
        target,
        confidence,
        save_file_folder,
        save_timestamped_file,
        camera_entity,
        name=None,
    ):
        """Init with the client."""
        self._client = client
        self._region = region
        self._target = target
        self._confidence = confidence
        self._save_file_folder = save_file_folder
        self._save_timestamped_file = save_timestamped_file
        self._camera_entity = camera_entity
        if name:  # Since name is optional.
            self._name = name
        else:
            entity_name = split_entity_id(camera_entity)[1]
            self._name = "{} {} {}".format("rekognition", target, entity_name)
        self._state = None  # The number of instances of interest
        self._last_detection = None  # The last time we detected something
        self._labels = {}  # The parsed label data

    def process_image(self, image):
        """Process an image."""
        self._state = None
        self._labels = {}

        response = self._client.detect_labels(Image={"Bytes": image})
        self._state = get_label_instances(response, self._target)
        self._labels = parse_labels(response)

        if self._state > 0:
            self._last_detection = dt_util.now().strftime(DATETIME_FORMAT)

        if self._save_file_folder and self._state > 0:
            self.save_image(
                image,
                response,
                self._target,
                self._confidence,
                self._save_file_folder,
                self._name,
            )

    @property
    def camera_entity(self):
        """Return camera entity id from process pictures."""
        return self._camera_entity

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attr = self._labels
        attr["target"] = self._target
        if self._last_detection:
            attr[f"last_{self._target.lower()}"] = self._last_detection
        return attr

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    def save_image(self, image, response, target, confidence, directory, camera_entity):
        """Draws the actual bounding box of the detected objects."""
        try:
            img = Image.open(io.BytesIO(bytearray(image))).convert("RGB")
        except UnidentifiedImageError:
            _LOGGER.warning("Sighthound unable to process image, bad data")
            return
        draw = ImageDraw.Draw(img)

        for label in response["Labels"]:
            if (label["Confidence"] < confidence) or (label["Name"] != target):
                continue

            for instance in label["Instances"]:
                box = instance["BoundingBox"]

                x, y, w, h = box["Left"], box["Top"], box["Width"], box["Height"]
                x_max, y_max = x + w, y + h

                box_label = f'{label["Name"]}: {label["Confidence"]:.1f}%'
                draw_box(
                    draw, (y, x, y_max, x_max), img.width, img.height, text=box_label,
                )

        latest_save_path = (
            directory / f"{get_valid_filename(self._name).lower()}_latest.jpg"
        )
        img.save(latest_save_path)

        if self._save_timestamped_file:
            timestamp_save_path = directory / f"{self._name}_{self._last_detection}.jpg"
            img.save(timestamp_save_path)
            _LOGGER.info("Deepstack saved file %s", timestamp_save_path)
