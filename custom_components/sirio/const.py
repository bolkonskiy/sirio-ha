"""Constants for the Sirio WinET controller integration."""

DOMAIN = "sirio"

CONF_HOST = "host"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_AUTO_SOFT_START = "auto_soft_start"

DEFAULT_SCAN_INTERVAL = 10
DEFAULT_SOFT_START_POLL_INTERVAL = 30
SOFT_START_REGISTER_INDEX = 17
SOFT_START_ENABLED_VALUE = 7

MANUFACTURER = "Sirio"
MODEL = "WinET Controller"

ATTR_STANDBY = "standby"
ATTR_ERROR_CODE = "error_code"
ATTR_SOFT_START = "soft_start"
