"""Layer 1 API for BUJJI SDK.

High-level Agent class that wires together:
- Hooks and policies for safety
- MCP servers for external tools
- ToolRunner for tool execution
- Conversation for stateful sessions
- Triggers for background tasks
- Memory for persistent storage
- Planner for task decomposition
- Router for confidence-based routing
"""

import contextlib
import logging

from bujji import types
from bujji.connections import connection as connection_module
from bujji.conversation import conversation
from bujji.hooks import hook_runner, hooks, policy
from bujji.mcp import bridge
from bujji.tools import tool_context, tool_runner
from bujji.triggers import trigger_runner, triggers as triggers_lib


class Agent:
    """High-level Agent API for simplified interaction.

    Wires hooks, policies, MCP, tools, conversation, triggers, memory,
    planner, and router behind a single async context manager.
    """

    def __init__(self, config: connection_module.AgentConfig):
        self._config = config.model_copy(deep=True)
        if self._config.response_schema:
            self._config.capabilities.finish_tool_schema_json = self._config.response_schema
        self._strategy = None
        self._conversation = None
        self._tool_runner = None
        self._hook_runner = None
        self._trigger_runner = None
        self._mcp_bridge = None
        self._memory = None
        self._planner = None
        self._router = None
        self._pending_hooks = list(config.hooks)
        self._pending_triggers = list(config.triggers)
        self._exit_stack = contextlib.AsyncExitStack()

    def register_hook(self, hook: hooks.Hook):
        if not self._hook_runner:
            self._pending_hooks.append(hook)
            return
        self._hook_runner.register_hook(hook)

    def register_trigger(self, trigger: triggers_lib.Trigger):
        if self._trigger_runner:
            raise RuntimeError("Cannot register triggers after the agent has started.")
        self._pending_triggers.append(trigger)

    async def __aenter__(self) -> "Agent":
        logging.info("Starting BUJJI Agent session")
        try:
            self._hook_runner = hook_runner.HookRunner()

            for hook in self._pending_hooks:
                self._hook_runner.register_hook(hook)
            self._pending_hooks.clear()

            active_policies = list(self._config.policies)
            if active_policies:
                self._hook_runner.register_hook(policy.enforce(active_policies))

            all_tools = list(self._config.tools)

            if self._config.mcp_servers:
                logging.info("Connecting to MCP servers...")
                self._mcp_bridge = bridge.McpBridge()
                self._exit_stack.push_async_callback(self._mcp_bridge.stop)
                for server_cfg in self._config.mcp_servers:
                    await self._mcp_bridge.connect(server_cfg)
                all_tools.extend(self._mcp_bridge.tools)

            self._tool_runner = tool_runner.ToolRunner(tools=all_tools)

            self._strategy = self._config.create_strategy(
                tool_runner=self._tool_runner,
                hook_runner=self._hook_runner,
            )

            logging.info("Starting connection and creating conversation...")
            self._conversation = await self._exit_stack.enter_async_context(
                conversation.Conversation.create(self._strategy)
            )

            if self._pending_triggers:
                logging.info("Starting triggers...")
                self._trigger_runner = await self._exit_stack.enter_async_context(
                    trigger_runner.TriggerRunner(
                        triggers=list(self._pending_triggers),
                        connection=self.conversation.connection,
                    )
                )
                self._pending_triggers.clear()

            if self._tool_runner:
                ctx = tool_context.ToolContext(self.conversation.connection)
                self._tool_runner.set_context(ctx)

            return self
        except Exception:
            logging.exception("Failed to start Agent session, cleaning up...")
            await self._exit_stack.aclose()
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logging.info("Stopping BUJJI Agent session")
        return await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    async def chat(self, prompt: types.Content) -> types.ChatResponse:
        return await self.conversation.chat(prompt)

    @property
    def is_started(self) -> bool:
        return self._conversation is not None

    @property
    def conversation(self) -> conversation.Conversation:
        if not self._conversation:
            raise RuntimeError("Agent session not started. Use 'async with Agent(...)'.")
        return self._conversation

    @property
    def conversation_id(self) -> str | None:
        if not self._conversation:
            return None
        return self._conversation.conversation_id or None
