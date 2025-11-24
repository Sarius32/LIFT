from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Requirement:
    id: str
    title: str
    description: str
    acceptance: str

    def to_dict(self):
        dict_ = OrderedDict()
        dict_["id"] = self.id
        dict_["title"] = self.title
        dict_["description"] = self.description
        dict_["acceptance"] = self.acceptance
        return dict_


@dataclass
class ReqScope:
    title: str
    scopes: list["ReqScope"] | None
    reqs: list[Requirement] | None

    @staticmethod
    def parse_yaml(yaml_data: list[dict] | dict) -> "ReqScope | None":
        for key, value in yaml_data.items():
            title = key
            scopes, reqs = None, None
            if isinstance(value, dict):
                scopes = [ReqScope.parse_yaml({k: v}) for k, v in value.items()]
            elif isinstance(value, list):
                reqs = [Requirement(**item) for item in value]

            return ReqScope(title, scopes, reqs)

        return None

    def to_dict(self):
        dict_ = OrderedDict()
        dict_["title"] = self.title
        if self.scopes:
            scope_dict = OrderedDict()
            for scope in self.scopes:
                scope_dict[scope.title] = scope.to_dict()
            dict_["scopes"] = scope_dict
        else:
            dict_["reqs"] = [req.to_dict() for req in self.reqs]

        return dict_

    def get_requirements(self) -> list[Requirement]:
        if self.reqs:
            return self.reqs

        reqs = []
        [reqs.extend(scope.get_requirements()) for scope in self.scopes]
        return reqs

    def find_requirement(self, id: str) -> Requirement | None:
        if self.reqs:
            for req in self.reqs:
                if req.id == id:
                    return req

        if self.scopes:
            for scope in self.scopes:
                req = scope.find_requirement(id)
                if req:
                    return req

        return None


_REQUIREMENTS: ReqScope


def parse_requirements_doc(file_path: Path) -> None:
    global _REQUIREMENTS

    with open(file_path) as req_file:
        req_data = yaml.safe_load(req_file)
    _REQUIREMENTS = ReqScope.parse_yaml(req_data)


def get_structured_reqs():
    return _REQUIREMENTS


def get_requirements_only():
    return _REQUIREMENTS.get_requirements()
