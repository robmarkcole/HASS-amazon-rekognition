"""
Platform that will perform object detection.
"""
import base64
import io
import json
import logging
import os
import re
import time
from datetime import timedelta
from PIL import Image, ImageDraw

import voluptuous as vol

from homeassistant.util.pil import draw_box
import homeassistant.util.dt as dt_util
from homeassistant.core import split_entity_id
import homeassistant.helpers.config_validation as cv
from homeassistant.components.image_processing import (
    PLATFORM_SCHEMA,
    ImageProcessingEntity,
    ATTR_CONFIDENCE,
    CONF_SOURCE,
    CONF_ENTITY_ID,
    CONF_NAME,
)


_LOGGER = logging.getLogger(__name__)

CONF_REGION = "region_name"
CONF_ACCESS_KEY_ID = "aws_access_key_id"
CONF_SECRET_ACCESS_KEY = "aws_secret_access_key"
CONF_SAVE_FILE_FOLDER = "save_file_folder"
CONF_TARGET = "target"
DEFAULT_TARGET = "Person"

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

REQUIREMENTS = ["boto3 == 1.9.69"]

SCAN_INTERVAL = timedelta(days=365)  # SCAN ONCE THEN NEVER AGAIN.

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(SUPPORTED_REGIONS),
        vol.Required(CONF_ACCESS_KEY_ID): cv.string,
        vol.Required(CONF_SECRET_ACCESS_KEY): cv.string,
        vol.Optional(CONF_TARGET, default=DEFAULT_TARGET): cv.string,
        vol.Optional(CONF_SAVE_FILE_FOLDER): cv.isdir,
    }
)


def get_label_instances(response, target):
    """Get the number of instances of a target label."""
    for label in response["Labels"]:
        if (
            label["Name"].lower() == target.lower()
        ):  # Lowercase both to prevent any comparing issues
            if len(label["Instances"]) > 0:
                return len(label["Instances"])
            else:
                return 1
    return 0


def parse_labels(response):
    """Parse the API labels data, returning objects only."""
    return {
        label["Name"]: round(label["Confidence"], 2) for label in response["Labels"]
    }


def get_valid_filename(name):
    return re.sub(r"(?u)[^-\w.]", "", str(name).strip().replace(" ", "_"))


def save_image(image, response, target, confidence, directory, camera_entity):
    """Draws the actual bounding box of the detected objects."""
    img = Image.open(io.BytesIO(bytearray(image))).convert("RGB")
    draw = ImageDraw.Draw(img)

    boxes = []
    for label in response["Labels"]:
        if (label["Confidence"] < confidence) or (label["Name"] != target):
            continue

        for instance in label["Instances"]:
            box = instance["BoundingBox"]

            x, y, w, h = box["Left"], box["Top"], box["Width"], box["Height"]
            x_max, y_max = x + w, y + h

            box_label = f'{label["Name"]}: {label["Confidence"]:.1f}%'
            draw_box(
                draw, (y, x, y_max, x_max), img.width, img.height, color=(0, 212, 0)
            )

            # Use draw for the text so you can give it a color that is actually readable
            left, top, line_width, font_height = (
                img.width * box["Left"],
                img.height * box["Top"],
                3,
                12,
            )
            draw.text(
                (left + line_width, abs(top - line_width - font_height)), box_label
            )

    latest_save_path = os.path.join(
        directory, get_valid_filename(camera_entity).lower() + "_latest.jpg"
    )
    img.save(latest_save_path)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up Rekognition."""

    import boto3

    aws_config = {
        CONF_REGION: config.get(CONF_REGION),
        CONF_ACCESS_KEY_ID: config.get(CONF_ACCESS_KEY_ID),
        CONF_SECRET_ACCESS_KEY: config.get(CONF_SECRET_ACCESS_KEY),
    }

    client = boto3.client("rekognition", **aws_config)  # Will not raise error.

    save_file_folder = config.get(CONF_SAVE_FILE_FOLDER)
    if save_file_folder:
        save_file_folder = os.path.join(save_file_folder, "")  # If no trailing / add it

    entities = []
    for camera in config[CONF_SOURCE]:
        entities.append(
            Rekognition(
                client,
                config.get(CONF_REGION),
                config.get(CONF_TARGET),
                config.get(ATTR_CONFIDENCE),
                save_file_folder,
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
        camera_entity,
        name=None,
    ):
        """Init with the client."""
        self._client = client
        self._region = region
        self._target = target
        self._confidence = confidence
        if save_file_folder:  # Since save_file_folder is optional.
            self._save_file_folder = save_file_folder
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
            self._last_detection = dt_util.now()

        if hasattr(self, "_save_file_folder"):  # Only save if folder is defined
            save_image(
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
            attr[
                "last_{}_detection".format(self._target)
            ] = self._last_detection.strftime("%Y-%m-%d %H:%M:%S")
        return attr

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name
