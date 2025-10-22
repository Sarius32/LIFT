from dataclasses import dataclass


@dataclass
class Agent:
    type_ = "agent"
    _logger = None

    _sys_prompt = ""
    _req_output = ""

    _messages = []


class Generator(Agent):
    ...


class Debugger(Agent):
    ...


class Evaluator(Agent):
    ...
