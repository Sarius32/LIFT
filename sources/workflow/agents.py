import json
from abc import abstractmethod, ABC
from pathlib import Path
from time import sleep
from typing import Any

from openai import OpenAI, RateLimitError
from openai.types.responses import ResponseOutputMessage, ResponseFunctionToolCall, ResponseReasoningItem, Response, \
    ResponseOutputText

import logging_
from env import API_KEY, GEN_MODEL, DEBUG_MODEL, EVAL_MODEL, PROJECT_PATH, REPORTS_PATH
from project_utils import ToolCallResult
from prompts import GEN_NAME, GEN_SYS_PROMPT, DEB_NAME, DEB_SYS_PROMPT, DEB_PROMPT, EVAL_NAME, EVAL_SYS_PROMPT, \
    EVAL_PROMPT
from tools import TOOLS_SPEC, TOOLS_IMPL

MAX_STEPS = 50
MAX_RETRIES = 5
REDACT_MAX_PREVIEW = 120


def _preview(s: str, limit: int = REDACT_MAX_PREVIEW) -> str:
    if len(s) <= limit:
        return s
    return f"{s[:limit]}... (+{len(s) - limit} more)"


def _redact_tool_args(name: str, args: dict) -> dict:
    """Return a log-safe copy of tool args."""
    a = dict(args or {})
    if name == "write_file" and "content" in a:
        # don't log file content in INFO; show length only
        a["content"] = f"<{len(a['content'])} chars>"
    if name == "replace_in_file":
        # avoid leaking long patterns; show lengths
        if "find" in a:
            a["find"] = f"<len {len(a['find'])}>"
        if "replace" in a:
            a["replace"] = f"<len {len(a['replace'])}>"
    # read_file/read_many/list_dir/delete_path are fine as-is
    return a


def _redact_tool_result(name: str, result: dict) -> dict:
    """Return a log-safe summary of tool outputs."""
    if not isinstance(result, dict):
        return {"summary": "<non-dict result>"}

    # if it's an error, log it as-is; it's short
    if "error" in result:
        return result

    if name == "read_file":
        # omit file contents; keep metadata
        return {
            "path": result["path"],
            "truncated": result["truncated"],
            "has_text": "text" in result,
            "has_base64": "base64_data" in result,
            "text_len": len(result["text"]) if "text" in result else None,
            "base64_len": len(result["base64_data"]) if ("base64_data" in result) else None,
        }

    if name == "read_many":
        # sanitize per-entry
        entries = []
        for e in result["entries"]:
            if "error" in e:
                entries.append(e)
            else:
                entries.append({
                    "path": e["path"],
                    "truncated": e["truncated"],
                    "has_text": "text" in e,
                    "has_base64": "base64_data" in e,
                    "text_len": len(e["text"]) if "text" in e else None,
                    "base64_len": len(e["base64_data"]) if ("base64_data" in e) else None,
                })
        return {"entries": entries}

    # write/delete/replace/list_dir: small payloads — log as-is
    return result


class Agent(ABC):
    type_ = "agent"

    def __init__(self, model: str, name: str, sys_prompt: str):
        self._model = model

        self._logger = logging_.get_logger("AGENT " + name)
        self._sys_prompt = sys_prompt

        self._logger.debug(f"System prompt: {_preview(repr(self._sys_prompt))}")
        self._messages = [{"role": "system", "content": self._sys_prompt}]

    @abstractmethod
    def _handle_end_conv_attempt(self, final_text: str) -> tuple[ToolCallResult, Any]:
        ...

    def _handle_tool_call(self, tool_call: ResponseFunctionToolCall) -> ToolCallResult:
        """ Handles a tool call by the agent. Returns the ToolCallResult."""
        end: ToolCallResult

        # get function & arguments
        name = tool_call.name
        args = json.loads(tool_call.arguments or "{}")
        self._logger.info(f"[TOOL CALL] - {name}({_redact_tool_args(name, args)})")

        # actually call function
        try:
            result = TOOLS_IMPL[name](**args)
            self._logger.info(f"[TOOL RESULT] - {name} -> {_redact_tool_result(name, result)}")
            end = ToolCallResult.CALL_SUCCEEDED

            # handle attempt to end conversation
            if name == "end_conversation":
                end, result = self._handle_end_conv_attempt(result)

        except Exception as e:
            result = {"error": str(e)}
            self._logger.error(f"[TOOL ERROR] - {name} failed: {e}")
            end = ToolCallResult.CALL_ERROR

        # append function call & response
        self._messages.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": json.dumps(result)
        })

        return end

    def query(self, instruction: str):
        self._logger.info(f"Calling with instruction: {_preview(repr(instruction))}")
        self._messages.append({"role": "user", "content": instruction})

        client = OpenAI(api_key=API_KEY)
        for step in range(MAX_STEPS):
            response = None
            for retry in range(MAX_RETRIES):
                try:
                    response: Response = client.responses.create(
                        model=self._model, input=self._messages,
                        tools=TOOLS_SPEC, tool_choice="auto", parallel_tool_calls=False, )
                    break
                except RateLimitError as e:
                    self._logger.info(
                        f"[RATE LIMIT HIT] - {e.message.split('{\'message\': \'')[1].split('Visit')[0].strip()}")

                    time = str(e.message).split("Please try again in")[1].strip().split("s")[0]
                    wait = 5
                    if "m" not in time:
                        wait += float(time.replace("m", ""))
                    self._logger.info(f"[RETRY #{retry}] - Waiting for {wait:.2f} secs")
                    sleep(wait)
                    self._logger.info(f"[RETRY #{retry}] - Waited for {wait:.2f} secs")

            if response is None:
                raise Exception("No response from model to process!")

            self._logger.info(f"[STATE #{step}] - Total tokens used: {response.usage.total_tokens}")

            for content in response.output:
                self._messages.append(content)

                if isinstance(content, ResponseOutputMessage):
                    message = content
                    for m_content in message.content:
                        if isinstance(m_content, ResponseOutputText):
                            self._logger.info(f"[RESPONSE MESSAGE] - {m_content.text}")
                        else:
                            self._logger.info(f"[RESPONSE MESSAGE REFUSAL] - {m_content.refusal}")

                elif isinstance(content, ResponseReasoningItem):
                    self._logger.info(f"[REASONING] - summary: {content.summary}, content: {content.content}")

                elif isinstance(content, ResponseFunctionToolCall):
                    end = self._handle_tool_call(content)
                    if end in [ToolCallResult.END_ACCEPTED, ToolCallResult.END_FINAL_SUITE,
                               ToolCallResult.END_REWORK_REQ]:
                        return end

                else:
                    self._logger.debug(f"[EVENT] - {content}")

        raise Exception(f"Conversation didn't terminate within {MAX_STEPS} steps!")


class Generator(Agent):
    type_ = GEN_NAME.lower()

    def __init__(self, iteration):
        super().__init__(GEN_MODEL, GEN_NAME + f" #{iteration:02d}", GEN_SYS_PROMPT)

    def _handle_end_conv_attempt(self, final_text: str):
        """ Returns END_ACCEPTED if <DONE> was sent else END_REJECTED. """
        if final_text != "<DONE>":
            self._logger.info(f"[CONTINUATION] - End message different than <DONE> found.")
            return ToolCallResult.END_REJECTED, dict(conversation_end=False,
                                                     reason="Only <DONE> as final_text expected.")

        self._logger.info(f"[AGENT CHAT END] - {final_text}")
        return ToolCallResult.END_ACCEPTED, dict(conversation_end=True)


class Debugger(Agent):
    type_ = DEB_NAME.lower()

    def __init__(self, iteration):
        super().__init__(DEBUG_MODEL, DEB_NAME + f" #{iteration:02d}", DEB_SYS_PROMPT)

    def query(self):
        return super().query(DEB_PROMPT)

    def _handle_end_conv_attempt(self, final_text: str):
        """ Returns END_ACCEPTED if <DONE> was sent and fixes.md exists else END_REJECTED. """
        if final_text != "<DONE>":
            self._logger.info(f"[CONTINUATION] - End message different than <DONE> found.")
            return ToolCallResult.END_REJECTED, dict(conversation_end=False,
                                                     reason="Only <DONE> as final_text expected.")

        if not Path(REPORTS_PATH / "fixes.md").exists():
            self._logger.info(f"[CONTINUATION] - Expected output fixes.md not found.")
            return ToolCallResult.END_REJECTED, dict(conversation_end=False,
                                                     reason="Expected output `fixes.md` missing.")

        self._logger.info(f"[AGENT CHAT END] - {final_text}")
        return ToolCallResult.END_ACCEPTED, dict(conversation_end=True)


class Evaluator(Agent):
    type_ = EVAL_NAME.lower()

    def __init__(self, iteration):
        super().__init__(EVAL_MODEL, EVAL_NAME + f" #{iteration:02d}", EVAL_SYS_PROMPT)

    def query(self):
        return super().query(EVAL_PROMPT)

    def _handle_end_conv_attempt(self, final_text: str):
        """ Returns END_REJECTED if <DONE> was not sent or fixes.md doesn't exist else (END_FINAL_SUITE if <FINAL> else END_REWORK_REQ). """
        if final_text not in ["<REWORK>", "<FINAL>"]:
            self._logger.info(f"[CONTINUATION] - End message different than <REWORK> or <FINAL> found.")
            return ToolCallResult.END_REJECTED, dict(conversation_end=False,
                                                     reason="Only <REWORK> or <FINAL> as final_text expected.")

        if not Path(REPORTS_PATH / "evaluation.md").exists():
            self._logger.info(f"[CONTINUATION] - Expected output evaluation.md not found.")
            return ToolCallResult.END_REJECTED, dict(conversation_end=False,
                                                     reason="Expected output `evaluation.md` missing.")

        if final_text == "<FINAL>":
            self._logger.info(f"[AGENT CHAT END] - {final_text}")
            return ToolCallResult.END_FINAL_SUITE, dict(conversation_end=True)

        self._logger.info(f"[AGENT CHAT END] - {final_text}")
        return ToolCallResult.END_REWORK_REQ, dict(conversation_end=True)
