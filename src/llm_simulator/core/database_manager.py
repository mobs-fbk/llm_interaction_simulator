from dataclasses import dataclass, field

from bson.objectid import ObjectId
from itakello_logging import ItakelloLogging
from pymongo.database import Database
from pymongo.errors import (
    ConfigurationError,
    OperationFailure,
    ServerSelectionTimeoutError,
)
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from ..abstracts import BaseManager
from ..components.conversation.conversation import Conversation
from ..components.conversation.message import Message
from ..components.experiment.experiment import Experiment
from ..utility.consts import DEFAULT_DATABASE, DEV_MODE
from ..utility.custom_os import CustomOS
from .input_manager import InputManager

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class DatabaseManager(BaseManager):
    input_m: InputManager

    username: str = field(init=False)
    db: Database = field(init=False)

    def __post_init__(self) -> None:
        self.username, client = self._ask_credentials()
        self._select_database(client)
        super().__post_init__()

    def _ask_credentials(self) -> tuple[str, MongoClient]:
        connected = False
        username = password = cluster_url = ""
        client = None
        while not connected:
            if CustomOS.getenv("APP_MODE", "") == DEV_MODE:
                username = CustomOS.getenv("DB_USER")
                password = CustomOS.getenv("DB_PASSWORD")
                cluster_url = CustomOS.getenv("DB_CLUSTER_URL")
            else:
                username = self.input_m.input_str("Enter your MongoDB username")
                password = self.input_m.password("Enter your MongoDB password")
                cluster_url = self.input_m.input_str("Enter your MongoDB cluster URL")
            try:
                client = MongoClient(
                    f"mongodb+srv://{username}:{password}@{cluster_url}/",
                    server_api=ServerApi("1"),
                )
            except Exception as e:
                logger.critical(f"Client error: {e}")
                raise e
            connected = self._check_connection(client)
        if client == None:
            logger.error("MongoDB client not created")
            raise ValueError("MongoDB client not created")
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
        except ServerSelectionTimeoutError:
            logger.critical(
                "Connection timeout. Ask the DB administrator to add your IP to the whitelist"
            )
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def _select_database(self, client: MongoClient) -> None:
        if CustomOS.getenv("APP_MODE", "") == "development":
            selected_db = "development"
        else:
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
        logger.debug(f"Databases found: {databases}")
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
        self,
        experiment: Experiment,
        conversation: Conversation,
        messages: list[Message],
    ) -> ObjectId:
        conversation.messages_ids = self._save_messages(messages)
        conversation_id = self.db.conversations.insert_one(
            conversation.to_document()
        ).inserted_id
        experiment.conversation_ids.append(conversation_id)
        self.update_experiment(experiment)
        logger.debug(f"Conversation saved with ID: {conversation_id}")
        return conversation_id

    def _save_messages(self, messages: list[Message]) -> list[ObjectId]:
        documents = [message.to_document() for message in messages]
        result = self.db.messages.insert_many(documents)
        message_ids = result.inserted_ids
        logger.debug(f"Messages saved with IDs: {message_ids}")
        return message_ids

    def add_conversation(self, experiment_id: ObjectId, conversation: ObjectId) -> None:
        self.db.experiments.update_one(
            {"_id": experiment_id},
            {"$push": {"conversations": conversation}},
        )
        logger.debug(f"Added conversation {conversation} to experiment {experiment_id}")

    def delete_experiment(self, experiment: Experiment) -> None:
        # Delete the conversations and messages associated with the experiment
        for conversation_id in experiment.conversation_ids:
            conversation_doc = self.db.conversations.find_one({"_id": conversation_id})
            conversation = Conversation.from_document(conversation_doc)
            self.db.messages.delete_many({"_id": {"$in": conversation.messages_ids}})
            self.db.conversations.delete_one({"_id": conversation_id})
            logger.debug(f"Deleted conversation with ID: {conversation_id}")
        self.db.experiments.delete_one({"_id": experiment.id})
        logger.debug(f"Deleted experiment with ID: {experiment.id}")

    def delete_conversation(self, conversation: Conversation) -> None:
        self.db.messages.delete_many({"_id": {"$in": conversation.messages_ids}})
        self.db.conversations.delete_one({"_id": conversation.id})
        logger.debug(f"Deleted conversation with ID: {conversation.id}")
