from copy import deepcopy
from dataclasses import dataclass, field

from itakello_logging import ItakelloLogging

from ...interfaces import BaseManager
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

    def ask_for_roles(
        self, private_sections: list[Section], default="guard, prisoner"
    ) -> list[Role]:
        assert all(
            section.type == SectionType.PRIVATE for section in private_sections
        ), logger.critical(
            f"Not all sections are of type {SectionType.PRIVATE.value.upper()}"
        )
        if CustomOS.getenv("APP_MODE", "") == "development":
            roles_names = CustomOS.getenv("ROLES").split(",")
        else:
            roles_names = self.input_m.input_list(
                "Enter the agent roles", example="guard, prisoner", default=default
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

    def ask_for_updated_roles(self, old_roles: dict[str, Role]) -> list[Role]:
        logger.instruction(
            instructions=[
                "The new roles will be appended to the existing one",
                "The roles that are not reinserted will be deleted",
            ]
        )

        old_private_sections_copy = self.get_private_sections_copy(old_roles)

        new_roles = self.ask_for_roles(
            old_private_sections_copy, default=", ".join(old_roles.keys())
        )
        for role in new_roles:
            if role.name in old_roles:
                role.sections = old_roles[role.name].sections
        return new_roles

    def get_private_sections_copy(self, roles: dict[str, Role]) -> list[Section]:
        private_sections_copy = deepcopy(
            list(list(roles.values())[0].sections.values())
        )
        for section in private_sections_copy:
            section.content = ""
            section.role = ""
            section.type = SectionType.PRIVATE
        return private_sections_copy
