from dataclasses import dataclass
from typing import List


@dataclass
class Requirement:
    id: str
    title: str
    description: str
    acceptance: str


def extract_reqs_from_yaml(obj: dict) -> List[Requirement]:
    """ Recursively collect Requirements in yaml input based on 'id' key. """
    found = []

    if isinstance(obj, dict):
        # If this dict *is* a requirement
        if "id" in obj:
            found.append(Requirement(**obj))

        # Recurse into values
        for value in obj.values():
            found.extend(extract_reqs_from_yaml(value))

    elif isinstance(obj, list):
        for item in obj:
            found.extend(extract_reqs_from_yaml(item))

    return found
