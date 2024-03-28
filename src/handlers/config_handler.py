import configparser
import logging

logger = logging.getLogger(__name__)


class ConfigHandler:
    def __init__(self, config_file="config/experiment_settings.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get_section(self, section):
        logger.debug(f"Retrieving section from config file: {section}")
        return dict(self.config[section])
