from enum import Enum
from typing import Any, Dict, List


def tool_metadata(description: str, properties: Dict[str, Any], required: List[str] = None):
    def decorator(fn):
        fn.name = fn.__name__.split("tool_")[-1]
        fn.description = description
        fn.properties = properties
        fn.required = required
        return fn

    return decorator


class ToolCallResult(Enum):
    CALL_SUCCEEDED = 0
    CALL_ERROR = 1
    END_ACCEPTED = 2
    END_REJECTED = 3
    END_FINAL_SUITE = 4
    END_REWORK_REQ = 5
