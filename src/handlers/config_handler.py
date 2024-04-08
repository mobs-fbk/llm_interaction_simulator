import logging
from configparser import ConfigParser
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ConfigHandler:
    config: ConfigParser = field(init=False)

    def __init__(self, config_file="config/settings.ini") -> None:
        self.config = ConfigParser()
        if not self.config.read(config_file):
            logger.error(f"Failed to read config file: {config_file}")
        logger.info(f"Config file read: {config_file}")

    def get_section(self, name: str) -> dict:
        logger.debug(f"Retrieved section: {name}")
        section = dict(self.config[name])
        return section
