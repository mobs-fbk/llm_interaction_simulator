from copy import deepcopy
from dataclasses import dataclass, field

from itakello_logging import ItakelloLogging

from ...abstracts import BaseManager
from ...core.input_manager import InputManager
from ...utility.custom_os import CustomOS
from ..placeholder.placeholder_manager import PlaceholderManager
from ..role.role import Role
from ..section.section import Section, SectionType
from ..section.section_manager import SectionManager

logger = ItakelloLogging().get_logger(__name__)


@dataclass
class RoleManager(BaseManager):
    input_m: InputManager
    section_m: SectionManager
    placeholder_m: PlaceholderManager

    def ask_for_roles(self, private_sections: list[Section]) -> list[Role]:
        assert all(
            section.type == SectionType.PRIVATE for section in private_sections
        ), logger.critical(
            f"Not all sections are of type {SectionType.PRIVATE.value.upper()}"
        )
        if CustomOS.getenv("APP_MODE", "") == "development":
            roles_names = CustomOS.getenv("ROLES").split(",")
        else:
            roles_names = self.input_m.input_list(
                "Enter the agent roles", example="guard, prisoner"
            )
        roles = []
        for name in roles_names:
            role_sections = deepcopy(private_sections)
            for section in role_sections:
                section.role = name
            new_role = Role(
                name=name,
                sections=role_sections,
            )
            roles.append(new_role)
        return roles
