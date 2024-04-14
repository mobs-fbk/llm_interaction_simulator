import json
import logging
from dataclasses import dataclass, field

from bson.objectid import ObjectId
from pymongo.database import Database
from pymongo.errors import ConfigurationError, OperationFailure
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from ..classes.conversation import Conversation
from ..classes.experiment import Experiment
from ..classes.message import Message

# from .config_handler import configurator

logger = logging.getLogger(__name__)


@dataclass
class DBHandler:
    client: MongoClient = field(init=False)
    db: Database = field(init=False)

    def __init__(self, username: str, password: str, cluster_url: str) -> None:
        try:
            self.client = MongoClient(
                f"mongodb+srv://{username}:{password}@{cluster_url}/",
                server_api=ServerApi("1"),
            )
            # Force a call to the server to establish a connection
            self.client.admin.command("ping")
            logger.debug("MongoDB connection established.")
        except ConfigurationError as e:
            raise ValueError("Invalid cluster URL") from e
        except OperationFailure as e:
            raise PermissionError("Authentication failed") from e

    def list_databases(self) -> list[str]:
        databases = self.client.list_database_names()
        databases.remove("admin")
        databases.remove("local")
        logger.debug(f"Available databases: {databases}")
        return databases

    def select_database(self, database: str) -> None:
        self.db = self.client[database]
        logger.debug(f"Selected database: {database}")

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
