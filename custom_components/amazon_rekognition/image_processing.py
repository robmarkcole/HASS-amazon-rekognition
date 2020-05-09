"""
Platform that will perform object detection.
"""
from collections import namedtuple
import io
import logging
import re
import time
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

DEFAULT_ROI_Y_MIN = 0.0
DEFAULT_ROI_Y_MAX = 1.0
DEFAULT_ROI_X_MIN = 0.0
DEFAULT_ROI_X_MAX = 1.0
DEFAULT_ROI = (
    DEFAULT_ROI_Y_MIN,
    DEFAULT_ROI_X_MIN,
    DEFAULT_ROI_Y_MAX,
    DEFAULT_ROI_X_MAX,
)


# rgb(red, green, blue)
RED = (255, 0, 0)  # For objects within the ROI
GREEN = (0, 255, 0)  # For ROI box
YELLOW = (255, 255, 0)  # For objects outside the ROI


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
CONF_TARGETS = "targets"
DEFAULT_TARGETS = ["person"]

CONF_ROI_Y_MIN = "roi_y_min"
CONF_ROI_X_MIN = "roi_x_min"
CONF_ROI_Y_MAX = "roi_y_max"
CONF_ROI_X_MAX = "roi_x_max"

CONF_SAVE_TIMESTAMPTED_FILE = "save_timestamped_file"
DATETIME_FORMAT = "%Y-%m-%d_%H:%M:%S"

CONF_BOTO_RETRIES = "boto_retries"
DEFAULT_BOTO_RETRIES = 5

REQUIREMENTS = ["boto3"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(SUPPORTED_REGIONS),
        vol.Required(CONF_ACCESS_KEY_ID): cv.string,
        vol.Required(CONF_SECRET_ACCESS_KEY): cv.string,
        vol.Optional(CONF_TARGETS, default=DEFAULT_TARGETS): vol.All(
            cv.ensure_list, [cv.string]
        ),
        vol.Optional(CONF_ROI_Y_MIN, default=DEFAULT_ROI_Y_MIN): cv.small_float,
        vol.Optional(CONF_ROI_X_MIN, default=DEFAULT_ROI_X_MIN): cv.small_float,
        vol.Optional(CONF_ROI_Y_MAX, default=DEFAULT_ROI_Y_MAX): cv.small_float,
        vol.Optional(CONF_ROI_X_MAX, default=DEFAULT_ROI_X_MAX): cv.small_float,
        vol.Optional(CONF_SAVE_FILE_FOLDER): cv.isdir,
        vol.Optional(CONF_SAVE_TIMESTAMPTED_FILE, default=False): cv.boolean,
        vol.Optional(CONF_BOTO_RETRIES, default=DEFAULT_BOTO_RETRIES): vol.All(
            vol.Coerce(int), vol.Range(min=0)
        ),
    }
)


Box = namedtuple("Box", "y_min x_min y_max x_max")
Point = namedtuple("Point", "y x")


def point_in_box(box: Box, point: Point) -> bool:
    """Return true if point lies in box"""
    if (box.x_min <= point.x <= box.x_max) and (box.y_min <= point.y <= box.y_max):
        return True
    return False


def object_in_roi(roi: dict, centroid: dict) -> bool:
    """Convenience to convert dicts to the Point and Box."""
    target_center_point = Point(centroid["y"], centroid["x"])
    roi_box = Box(roi["y_min"], roi["x_min"], roi["y_max"], roi["x_max"])
    return point_in_box(roi_box, target_center_point)


def get_objects(response: str) -> dict:
    """Parse the data, returning detected objects only."""
    objects = []
    decimal_places = 3

    for label in response["Labels"]:
        if len(label["Instances"]) > 0:
            for instance in label["Instances"]:
                # Extract and format instance data
                box = instance["BoundingBox"]
                # Get bounding box
                x_min, y_min, width, height = (
                    box["Left"],
                    box["Top"],
                    box["Width"],
                    box["Height"],
                )
                x_max, y_max = x_min + width, y_min + height

                bounding_box = {
                    "x_min": round(x_min, decimal_places),
                    "y_min": round(y_min, decimal_places),
                    "x_max": round(x_max, decimal_places),
                    "y_max": round(y_max, decimal_places),
                    "width": round(box["Width"], decimal_places),
                    "height": round(box["Height"], decimal_places),
                }

                # Get box area (% of frame)
                box_area = width * height * 100

                # Get box centroid
                centroid_x, centroid_y = (x_min + width / 2), (y_min + height / 2)
                centroid = {
                    "x": round(centroid_x, decimal_places),
                    "y": round(centroid_y, decimal_places),
                }

                objects.append(
                    {
                        "name": label["Name"].lower(),
                        "confidence": round(instance["Confidence"], decimal_places),
                        "bounding_box": bounding_box,
                        "box_area": round(box_area, decimal_places),
                        "centroid": centroid,
                    }
                )
    return objects


def get_valid_filename(name: str) -> str:
    return re.sub(r"(?u)[^-\w.]", "", str(name).strip().replace(" ", "_"))


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up ObjectDetection."""

    import boto3

    _LOGGER.debug("boto_retries setting is {}".format(config[CONF_BOTO_RETRIES]))

    aws_config = {
        CONF_REGION: config[CONF_REGION],
        CONF_ACCESS_KEY_ID: config[CONF_ACCESS_KEY_ID],
        CONF_SECRET_ACCESS_KEY: config[CONF_SECRET_ACCESS_KEY],
    }

    retries = 0
    success = False
    while retries <= config[CONF_BOTO_RETRIES]:
        try:
            client = boto3.client("rekognition", **aws_config)
            success = True
            break
        except KeyError:
            _LOGGER.info("boto3 client failed, retries={}".format(retries))
            retries += 1
            time.sleep(1)

    if not success:
        raise Exception(
            "Failed to create boto3 client. Maybe try increasing "
            "the boto_retries setting. Retry counter was {}".format(retries)
        )

    save_file_folder = config.get(CONF_SAVE_FILE_FOLDER)
    if save_file_folder:
        save_file_folder = Path(save_file_folder)

    targets = [t.lower() for t in config[CONF_TARGETS]]  # ensure lower case

    entities = []
    for camera in config[CONF_SOURCE]:
        entities.append(
            ObjectDetection(
                client,
                config[CONF_REGION],
                targets,
                config[ATTR_CONFIDENCE],
                config[CONF_ROI_Y_MIN],
                config[CONF_ROI_X_MIN],
                config[CONF_ROI_Y_MAX],
                config[CONF_ROI_X_MAX],
                save_file_folder,
                config[CONF_SAVE_TIMESTAMPTED_FILE],
                camera[CONF_ENTITY_ID],
                camera.get(CONF_NAME),
            )
        )
    add_devices(entities)


class ObjectDetection(ImageProcessingEntity):
    """Perform object and label recognition."""

    def __init__(
        self,
        client,
        region,
        targets,
        confidence,
        roi_y_min,
        roi_x_min,
        roi_y_max,
        roi_x_max,
        save_file_folder,
        save_timestamped_file,
        camera_entity,
        name=None,
    ):
        """Init with the client."""
        self._aws_client = client
        self._aws_region = region
        self._targets = targets
        self._confidence = confidence
        self._roi_y_min = roi_y_min
        self._roi_x_min = roi_x_min
        self._roi_y_max = roi_y_max
        self._roi_x_max = roi_x_max
        self._roi_dict = {
            "y_min": roi_y_min,
            "x_min": roi_x_min,
            "y_max": roi_y_max,
            "x_max": roi_x_max,
        }
        self._save_file_folder = save_file_folder
        self._save_timestamped_file = save_timestamped_file
        self._camera_entity = camera_entity
        if name:  # Since name is optional.
            self._name = name
        else:
            entity_name = split_entity_id(camera_entity)[1]
            self._name = f"rekognition_{entity_name}"
        self._state = None  # The number of instances of interest
        self._last_detection = None  # The last time we detected a target
        self._objects = []  # The parsed raw data
        self._targets_found = []  # The filtered targets data

    def process_image(self, image):
        """Process an image."""
        self._state = None
        self._objects = []
        self._targets_found = []

        response = self._aws_client.detect_labels(Image={"Bytes": image})
        self._objects = get_objects(response)
        self._targets_found = [
            obj
            for obj in self._objects
            if (obj["name"] in self._targets)
            and (obj["confidence"] > self._confidence)
            and (object_in_roi(self._roi_dict, obj["centroid"]))
        ]
        self._state = len(self._targets_found)

        if self._state > 0:
            self._last_detection = dt_util.now().strftime(DATETIME_FORMAT)

        if self._save_file_folder and self._state > 0:
            self.save_image(
                image,
                response,
                self._targets,
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
        attr = {}
        for target in self._targets:
            attr[f"ROI {target} count"] = len(
                [t for t in self._targets_found if t["name"] == target]
            )
            attr[f"ALL {target} count"] = len(
                [t for t in self._objects if t["name"] == target]
            )
        attr["last_target_detection"] = self._last_detection
        attr["objects"] = self._objects
        return attr

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    def save_image(
        self, image, response, targets, confidence, directory, camera_entity
    ):
        """Draws the actual bounding box of the detected objects."""
        try:
            img = Image.open(io.BytesIO(bytearray(image))).convert("RGB")
        except UnidentifiedImageError:
            _LOGGER.warning("Rekognition unable to process image, bad data")
            return
        draw = ImageDraw.Draw(img)

        # Draw ROI only if configured and not default
        roi = (
            self._roi_y_min,
            self._roi_x_min,
            self._roi_y_max,
            self._roi_x_max,
        )  # Tuple
        if roi != DEFAULT_ROI:
            draw_box(
                draw, roi, img.width, img.height, text="ROI", color=GREEN,
            )

        for obj in self._objects:
            if not obj["name"] in self._targets:
                pass
            name = obj["name"]
            confidence = obj["confidence"]
            box = obj["bounding_box"]
            centroid = obj["centroid"]

            if object_in_roi(self._roi_dict, centroid):
                box_colour = RED
            else:
                box_colour = YELLOW

            box_label = f"{name}: {confidence:.1f}%"
            draw_box(
                draw,
                (box["y_min"], box["x_min"], box["y_max"], box["x_max"]),
                img.width,
                img.height,
                text=box_label,
                color=box_colour,
            )

            # draw bullseye
            draw.text(
                (centroid["x"] * img.width, centroid["y"] * img.height),
                text="X",
                fill=box_colour,
            )

        latest_save_path = (
            directory / f"{get_valid_filename(self._name).lower()}_latest.jpg"
        )
        img.save(latest_save_path)

        if self._save_timestamped_file:
            timestamp_save_path = directory / f"{self._name}_{self._last_detection}.jpg"
            img.save(timestamp_save_path)
            _LOGGER.info("Rekognition saved file %s", timestamp_save_path)
