import json
import logging
from dataclasses import dataclass, field

from bson.objectid import ObjectId
from pymongo.database import Database
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from ..classes.conversation import Conversation
from ..classes.experiment import Experiment
from ..classes.message import Message
from .config_handler import configurator

logger = logging.getLogger(__name__)


@dataclass
class DBHandler:
    config: dict = field(init=False)
    db: Database = field(init=False)

    def __init__(self) -> None:
        self.config = configurator.get_section(name="Database")
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

    def get_conversations(self, conversation_ids: list[ObjectId]) -> list[dict]:
        # Retrieve the conversations from the database
        conversations = list(
            self.db.conversations.find({"_id": {"$in": conversation_ids}})
        )
        logger.debug(f"Conversations retrieved: {len(conversations)}")
        return conversations

    def get_experiment(self, experiment_id: str) -> Experiment:
        config = self.db.experiments.find_one({"_id": ObjectId(experiment_id)})
        logger.debug(f"Experiment retrieved: {experiment_id}")
        experiment = Experiment(config=config)  # type: ignore
        return experiment

    def get_conversation(self, conversation_id: str) -> dict:
        config = self.db.conversations.find_one({"_id": ObjectId(conversation_id)})
        logger.debug(f"Conversation retrieved: {conversation_id}")
        return config  # type: ignore

    def update_experiment(self, experiment: Experiment) -> None:
        self.db.experiments.update_one(
            {"_id": experiment.id},
            {"$set": experiment.to_document()},
        )
        logger.debug(f"Experiment updated with ID: {experiment.id}")

    def update_conversation(self, conversation: dict) -> None:
        self.db.conversations.update_one(
            {"_id": conversation["_id"]},
            {"$set": conversation},
        )
        logger.debug(f"Conversation updated with ID: {conversation['_id']}")

    def save_experiment(self, experiment: Experiment) -> ObjectId:
        experiment_id = self.db.experiments.insert_one(
            experiment.to_document()
        ).inserted_id
        logger.debug(f"Experiment saved with ID: {experiment_id}")
        return experiment_id

    def save_conversation(self, conversation: Conversation) -> ObjectId:
        for message in conversation.messages_ids:
            if isinstance(message, Message):
                message.id = self._save_message(message)
            else:
                logger.error(f"Invalid message type: {type(message)}")
        conversation_id = self.db.conversations.insert_one(
            conversation.to_document()
        ).inserted_id
        logger.debug(f"Conversation saved with ID: {conversation_id}")
        return conversation_id

    def _save_message(self, message: Message) -> ObjectId:
        message_id = self.db.messages.insert_one(message.to_document()).inserted_id
        logger.debug(f"Message saved with ID: {message_id}")
        return message_id

    def add_conversation(self, experiment_id: ObjectId, conversation: ObjectId) -> None:
        self.db.experiments.update_one(
            {"_id": experiment_id},
            {"$push": {"conversations": conversation}},
        )
        logger.debug(f"Added conversation {conversation} to experiment {experiment_id}")

    def delete_experiment(self, experiment: Experiment) -> None:
        # Delete the conversations and messages associated with the experiment
        for conversation_id in experiment.conversations_ids:
            conversation = self.db.conversations.find_one({"_id": conversation_id})
            for message in conversation["messages"]:  # type: ignore
                self.db.messages.delete_one({"_id": message})
            self.db.conversations.delete_one({"_id": conversation_id})
            logger.debug(f"Deleted conversation with ID: {conversation_id}")
        self.db.experiments.delete_one({"_id": experiment.id})
        logger.debug(f"Deleted experiment with ID: {experiment.id}")

    def delete_conversation(self, conversation: dict) -> None:
        for message in conversation["messages"]:
            self.db.messages.delete_one({"_id": message})
        self.db.conversations.delete_one({"_id": conversation["_id"]})
        logger.debug(f"Deleted conversation with ID: {conversation['_id']}")

    def get_messages(self, message_ids: list[ObjectId]) -> list[dict]:
        messages = list(self.db.messages.find({"_id": {"$in": message_ids}}))
        logger.debug(f"Messages retrieved: {len(messages)}")
        return messages
