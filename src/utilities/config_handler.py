import configparser
import logging


class ConfigHandler:
    def __init__(self, config_file="config/experiment_settings.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get_section(self, section):
        logging.debug(f"Retrieving section: {section}")
        return dict(self.config[section])
