import os
from dataclasses import dataclass, field

from bson.objectid import ObjectId
from itakello_logging import ItakelloLogging
from pymongo.database import Database
from pymongo.errors import ConfigurationError, OperationFailure
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from ..conversations.conversation import Conversation
from ..experiments.experiment import Experiment
from ..messages.message import Message
from ..utility.consts import DEFAULT_DATABASE
from .input_m import InputManager

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class DatabaseManager:
    input_m: InputManager = field(default_factory=InputManager)
    username: str = field(init=False)
    db: Database = field(init=False)

    def __post_init__(self) -> None:
        self.username, client = self._ask_credentials()
        self._select_database(client)
        logger.debug("Database manager initialized")

    def _ask_credentials(self) -> tuple[str, MongoClient]:
        connected = False
        app_mode = os.getenv("APP_MODE", "production")
        username = password = cluster_url = ""
        client = None
        while not connected:
            if app_mode == "production":
                username = self.input_m.input_str("Enter your username")
                password = self.input_m.password("Enter your password")
                cluster_url = self.input_m.input_str("Enter your MongoDB cluster URL")
            else:
                username = os.getenv("DB_USER", "default_username")
                password = os.getenv("DB_PASSWORD", "default_password")
                cluster_url = os.getenv("DB_CLUSTER_URL", "default_cluster_url")
            client = MongoClient(
                f"mongodb+srv://{username}:{password}@{cluster_url}/",
                server_api=ServerApi("1"),
            )
            connected = self._check_connection(client)
        if client == None:
            logger.error("MongoDB client not created")
            exit()
        logger.debug(f"MongoDB client created with address [{client.address}].")
        return username, client

    def _check_connection(self, client: MongoClient) -> bool:
        try:
            client.admin.command("ping")
            logger.confirmation("MongoDB connection established.")
            return True
        except ConfigurationError:
            logger.error("Invalid cluster URL")
            return False
        except OperationFailure:
            logger.error("Authentication failed")
            return False

    def _select_database(self, client: MongoClient) -> None:
        databases = self._list_databases(client)
        if not databases:
            selected_db = DEFAULT_DATABASE
            logger.warning(
                f"No databases found. Creating a new one named {selected_db}."
            )
        else:
            selected_db = self.input_m.select_one("Select a database", databases)
        self.db = client[selected_db]
        logger.debug(f"Selected database: {selected_db}")

    def _list_databases(self, client: MongoClient) -> list[str]:
        databases = client.list_database_names()
        databases.remove("admin")
        databases.remove("local")
        return databases

    def save_experiment(self, experiment: Experiment) -> None:
        self.db.experiments.insert_one(experiment.to_document())
        logger.debug(f"Experiment saved with ID: {experiment.id}")

    def get_experiments(self) -> dict[str, Experiment]:
        experiment_docs = list(self.db.experiments.find())
        experiments = {
            str(doc["_id"]): Experiment.from_document(doc) for doc in experiment_docs
        }
        logger.debug(f"Experiments retrieved: {len(experiments)}")
        return experiments

    def get_conversations(
        self, conversation_ids: list[ObjectId]
    ) -> dict[str, Conversation]:
        # Retrieve the conversations from the database
        conversation_docs = list(
            self.db.conversations.find({"_id": {"$in": conversation_ids}})
        )
        conversations = {
            str(doc["_id"]): Conversation.from_document(doc)
            for doc in conversation_docs
        }
        logger.debug(f"Conversations retrieved: {len(conversation_docs)}")
        return conversations

    def get_messages(self, message_ids: list[ObjectId]) -> dict[str, Message]:
        # Retrieve the messages from the database
        message_docs = list(self.db.messages.find({"_id": {"$in": message_ids}}))
        messages = {str(doc["_id"]): Message.from_document(doc) for doc in message_docs}
        logger.debug(f"Messages retrieved: {len(message_docs)}")
        return messages

    def update_experiment(self, experiment: Experiment) -> None:
        self.db.experiments.update_one(
            {"_id": experiment.id},
            {"$set": experiment.to_document()},
        )
        logger.debug(f"Experiment updated with ID: {experiment.id}")

    def update_conversation(self, conversation: Conversation) -> None:
        self.db.conversations.update_one(
            {"_id": conversation.id},
            {"$set": conversation.to_document()},
        )
        logger.debug(f"Conversation updated with ID: {conversation.id}")

    def save_conversation(
        self, experiment: Experiment, conversation: Conversation
    ) -> ObjectId:
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
        for conversation_id in experiment.conversation_ids:
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
