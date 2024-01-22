import configparser

class ConfigHandler:
    def __init__(self, config_file='experiment_settings.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get_section(self, section):
        return dict(self.config[section])