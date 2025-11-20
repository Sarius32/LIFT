import json
from time import sleep

from openai import OpenAI, RateLimitError

from openai.types.responses import ResponseOutputMessage, ResponseFunctionToolCall, ResponseReasoningItem, Response, \
    ResponseOutputText

import logging_
from env import API_KEY, MODEL
from tools import TOOLS_SPEC, TOOLS_IMPL, tool_list_dir
from prompts import GEN_NAME, GEN_SYS_PROMPT, DEB_NAME, DEB_SYS_PROMPT, DEB_PROMPT, EVAL_NAME, EVAL_SYS_PROMPT, \
    EVAL_PROMPT

MAX_STEPS = 50
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


class Agent:
    type_ = "agent"

    def __init__(self, name: str, sys_prompt: str, req_output: str = None):
        self._logger = logging_.get_logger("AGENT " + name)
        self._sys_prompt = sys_prompt
        self._req_output = req_output

        self._logger.debug(f"System prompt: {_preview(repr(self._sys_prompt))}")
        self._messages = [
            {"role": "system", "content": self._sys_prompt},
        ]

    def query(self, instruction: str):
        self._logger.info(f"Calling with instruction: {_preview(repr(instruction))}")
        self._messages.append({"role": "user", "content": instruction})

        client = OpenAI(api_key=API_KEY)
        not_exit = 0
        for step in range(MAX_STEPS):
            response = None
            for _ in range(5):
                try:
                    response: Response = client.responses.create(
                        model=MODEL,
                        instructions=self._sys_prompt,
                        input=self._messages,
                        tools=TOOLS_SPEC,
                        tool_choice="auto",
                        parallel_tool_calls=False,
                    )
                    break
                except RateLimitError as e:
                    self._logger.info(
                        f"[RATE LIMIT HIT] - {e.message.split('{\'message\': \'')[1].split('Visit')[0].strip()}")

                    time = str(e.message).split("Please try again in")[1].strip().split("s")[0]
                    wait = 5
                    if "m" not in time:
                        wait += float(time.replace("m", ""))
                    self._logger.info(f"[RETRY] - Waiting for {wait:.2f} secs")
                    sleep(wait)
                    self._logger.info(f"[RETRY] - Waited for {wait:.2f} secs")

            if response is None:
                raise Exception("No response from model to process!")

            self._logger.info(f"[STATE] - Total tokens used: {response.usage.total_tokens}")

            for content in response.output:
                self._messages.append(content)

                if isinstance(content, ResponseOutputMessage):
                    for c in content.content:
                        if isinstance(c, ResponseOutputText):
                            self._logger.info(f"[RESPONSE MESSAGE] - {c.text}")

                            if c.text in ["<DONE>", "<FINAL>", "<REWORK>"]:  # Conversation End found
                                if self._req_output:
                                    entries = tool_list_dir(glob=self._req_output)["entries"]
                                    if any([self._req_output in e["path"] for e in entries]) or not_exit > 4:
                                        return c.text
                                    else:
                                        self._messages.append({"role": "user",
                                                               "content": f"Expected output `{self._req_output}` was not found/created. Do that before finishing the task!"})
                                        self._logger.info(
                                            f"[CONTINUATION] - The exit was rejected since the required output `{self._req_output}` was not created.")
                                        not_exit += 1
                                        continue
                                return c.text

                            if "<DONE>" in c.text or "<FINAL>" in c.text or "<REWORK>" in c.text:  # Conversation End
                                self._messages.append({"role": "user",
                                                       "content": "If you deem your task to be completed, please only send `<DONE>` or `<FINAL>` or `<REWORK>`!"})
                                self._logger.info(
                                    f"[CONTINUATION] - Exit flag found in larger text message. Forcing correct format!")

                        else:
                            self._logger.info(f"[RESPONSE MESSAGE REFUSAL] - {c.refusal}")

                elif isinstance(content, ResponseReasoningItem):
                    self._logger.info(f"[REASONING] - summary: {content.summary}, content: {content.content}")

                elif isinstance(content, ResponseFunctionToolCall):
                    # get function & arguments
                    name = content.name
                    args = json.loads(content.arguments or "{}")
                    self._logger.info(f"[TOOL CALL] - {name}({_redact_tool_args(name, args)})")

                    # actually call function
                    try:
                        result = TOOLS_IMPL[name](**args)
                        self._logger.info(f"[TOOL RESULT] - {name} -> {_redact_tool_result(name, result)}")
                    except Exception as e:
                        result = {"error": str(e)}
                        self._logger.error(f"[TOOL ERROR] - {name} failed: {e}")

                    # append function call & response
                    self._messages.append({
                        "type": "function_call_output",
                        "call_id": content.call_id,
                        "output": json.dumps(result)
                    })

                else:
                    self._logger.debug(f"[EVENT] - {content}")

        return ""


class Generator(Agent):
    type_ = GEN_NAME.lower()

    def __init__(self, iteration):
        super().__init__(GEN_NAME + f" #{iteration:02d}", GEN_SYS_PROMPT)


class Debugger(Agent):
    type_ = DEB_NAME.lower()

    def __init__(self, iteration):
        super().__init__(DEB_NAME + f" #{iteration:02d}", DEB_SYS_PROMPT, "fixes.md")

    def query(self):
        return super().query(DEB_PROMPT)


class Evaluator(Agent):
    type_ = EVAL_NAME.lower()

    def __init__(self, iteration):
        super().__init__(EVAL_NAME + f" #{iteration:02d}", EVAL_SYS_PROMPT, "evaluation.md")

    def query(self):
        return super().query(EVAL_PROMPT)
