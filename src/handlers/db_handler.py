import datetime
import json
import logging
from dataclasses import dataclass, field

from bson.objectid import ObjectId
from pymongo.database import Database
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from ..classes.conversation import Conversation

logger = logging.getLogger(__name__)


@dataclass
class DBHandler:
    config: dict = field(init=False)
    db: Database = field(init=False)

    def __init__(self, config: dict) -> None:
        self.config = config
        self.db = self._get_db(self.config["db_name"])
        logger.debug(
            f"Connected to the database with config:\n {json.dumps(self.config, indent=2)}"
        )

    def _get_db(self, db_name: str) -> Database:
        uri = self._get_db_uri()
        client = MongoClient(uri, server_api=ServerApi("1"))
        db = client[db_name]
        logger.debug(f"Database: [{db_name}] selected")
        return db

    def _get_db_uri(self) -> str:
        uri = "mongodb+srv://<user>:<password>@<cluster_url>/?retryWrites=true&w=majority&appName=Cluster0"
        uri = uri.replace("<user>", self.config["user"])
        uri = uri.replace("<password>", self.config["password"])
        uri = uri.replace("<cluster_url>", self.config["cluster_url"])
        logger.debug(f"Database URI: {uri}")
        return uri

    def get_experiments(self) -> list[dict]:
        experiments = list(self.db.experiments.find())
        logger.debug(f"Experiments retrieved: {len(experiments)}")
        return experiments

    def save_experiment(self, doc: dict) -> ObjectId:
        doc["timestamp"] = datetime.datetime.now()
        doc["user"] = self.config["user"]
        experiment_id = self.db.experiments.insert_one(doc).inserted_id
        logger.debug(f"Experiment saved with ID: {experiment_id}")
        return experiment_id

    def save_conversation(
        self, experiment_id: ObjectId, conversation: Conversation
    ) -> None:
        for message in conversation.messages:
            message_doc = message.to_document()
            message_doc["experiment_id"] = experiment_id
            message_id = self.db.messages.insert_one(message_doc).inserted_id
            logger.debug(f"Message saved with ID: {message_id}")
        logger.debug("Conversation saved")
