from abc import ABC, abstractmethod
from typing import Any


class MongoModel(ABC):

    @abstractmethod
    def to_document(self) -> dict | str:
        """
        Converts the object to a dictionary representation.

        Returns:
            dict: A dictionary representation of the object.
        """
        pass

    @classmethod
    @abstractmethod
    def from_document(cls, doc: dict) -> Any:
        """
        Converts a dictionary representation to an object.

        Args:
            doc (dict): A dictionary representation of the object.

        Returns:
            DocumentSerializer: An object representation of the dictionary.
        """
        pass
