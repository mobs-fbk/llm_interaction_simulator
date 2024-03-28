import datetime
import json
import logging
from dataclasses import dataclass, field

from pymongo.database import Database
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from ..classes import Conversation
from . import ConfigHandler

logger = logging.getLogger(__name__)


@dataclass
class DatabaseHandler:
    config: dict = field(init=False)
    db: Database = field(init=False)

    def __post_init__(self):
        self.config = ConfigHandler().get_section("Database")
        uri = self._get_db_uri()
        client = MongoClient(uri, server_api=ServerApi("1"))
        self.db = client[self.config["db_name"]]
        logger.info(
            f"Connected to the database with config:\n {json.dumps(self.config, indent=2)}"
        )

    def _get_db_uri(self) -> str:
        uri = "mongodb+srv://<user>:<password>@<cluster_url>/?retryWrites=true&w=majority&appName=Cluster0"
        uri = uri.replace("<user>", self.config["user"])
        uri = uri.replace("<password>", self.config["password"])
        uri = uri.replace("<cluster_url>", self.config["cluster_url"])
        logger.debug(f"Database URI: {uri}")
        return uri

    def save_experiment(self, doc: dict) -> str:
        doc["timestamp"] = datetime.datetime.now()
        doc["user"] = self.config["user"]
        experiment_id = self.db.experiments.insert_one(doc).inserted_id
        logger.info(f"Experiment saved with ID: {experiment_id}")
        return experiment_id

    def save_conversation(self, experiment_id: str, conversation: Conversation) -> None:
        pass
        logger.info("Conversation saved")
        """for message in conversation:
            message["experiment_id"] = experiment_id
            message["timestamp"] = datetime.datetime.now()
        self.db.conversations.insert_many(conversation)
        return"""
