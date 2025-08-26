import os
import logging
import time
import json
from typing import Dict, Any, Optional, Union
from contextlib import contextmanager
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from app.config import config
from app.google_agent.agent_prompts import AgentPrompts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Centralized Model Selection ---
provider = (config.LLM_PROVIDER or "openai").lower()
if provider == "azure":
    REASONING_MODEL = config.AZURE_REASONING_MODEL
    SUMMARIZING_MODEL = config.AZURE_SUMMARIZING_MODEL
    PLANNER_MODEL = config.AZURE_PLANNER_MODEL
    BASE_MODEL_PARAMS = {
        "temperature": 1.0,
        "max_completion_tokens": 2000,
        "drop_params": True,
        "stream": False,
        "api_base": config.AZURE_OPENAI_ENDPOINT,
        "api_key": config.AZURE_OPENAI_KEY,
        "api_version": config.AZURE_OPENAI_API_VERSION,
    }
elif provider == "openai":
    REASONING_MODEL = config.OPENAI_REASONING_MODEL
    SUMMARIZING_MODEL = config.OPENAI_SUMMARIZING_MODEL
    PLANNER_MODEL = config.OPENAI_PLANNER_MODEL
    BASE_MODEL_PARAMS = {
        "temperature": 1.0,
        "max_completion_tokens": 2000,
        "drop_params": True,
        "stream": False,
        # OPENAI_API_KEY is picked up by LiteLlm automatically
    }
else:
    raise ValueError(f"Unsupported LLM_PROVIDER: {config.LLM_PROVIDER}")

# --- MCP Tool Import ---
try:
    from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
    mcp_available = True
    print("[AGENT] Successfully imported MCP tools from session_manager")
except ImportError:
    print("Warning: MCP toolset imports failed, disabling MCP tools")
    mcp_available = False
    MCPToolset = object
    SseServerParams = None

# --- Startup Logging ---
print("=" * 80)
print("[AGENT STARTUP] LLM Provider Configuration:")
print(f"[AGENT STARTUP] Provider: {config.LLM_PROVIDER.upper()}")

if provider == "azure":
    print(f"[AGENT STARTUP] Azure Endpoint: {config.AZURE_OPENAI_ENDPOINT or 'Not Set'}")
    print(f"[AGENT STARTUP] Azure API Version: {config.AZURE_OPENAI_API_VERSION or 'Not Set'}")
    print(f"[AGENT STARTUP] Reasoning Model: {REASONING_MODEL}")
    print(f"[AGENT STARTUP] Summarizing Model: {SUMMARIZING_MODEL}")
    print(f"[AGENT STARTUP] Planner Model: {PLANNER_MODEL}")
    azure_key_status = "Set" if config.AZURE_OPENAI_KEY else "Not Set"
    print(f"[AGENT STARTUP] Azure API Key: {azure_key_status}")
elif provider == "openai":
    print(f"[AGENT STARTUP] Reasoning Model: {REASONING_MODEL}")
    print(f"[AGENT STARTUP] Summarizing Model: {SUMMARIZING_MODEL}")
    print(f"[AGENT STARTUP] Planner Model: {PLANNER_MODEL}")
    openai_key_status = "Set" if config.OPENAI_API_KEY else "Not Set"
    print(f"[AGENT STARTUP] OpenAI API Key: {openai_key_status}")
else:
    print("[AGENT STARTUP] Unknown provider configuration!")

# --- Per-Agent Model Assignment ---
AGENT_MODEL_MAP = {
    'root_agent': REASONING_MODEL,
    'question_answer_summary_agent': SUMMARIZING_MODEL,
    'sloka_level_agent': REASONING_MODEL,
    'ramayana_summary_agent': SUMMARIZING_MODEL,
    'mahabharata_summary_agent': SUMMARIZING_MODEL,
    'bhagavatham_summary_agent': SUMMARIZING_MODEL,
    'specialized_helper_agent': PLANNER_MODEL,
}
MODEL_PARAMS = {
    'root_agent': {"max_completion_tokens": 1600},
    'question_answer_summary_agent': {"max_completion_tokens": 2000},
    # Add more per-agent params as needed
}

print("[AGENT STARTUP] Per-Agent Model Assignments:")
for agent_name, model_name in AGENT_MODEL_MAP.items():
    print(f"  {agent_name}: {model_name}")
print("=" * 80)

class SafeAgentTracer:
    """Safe, lightweight tracing that won't break existing functionality"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent_trace.{agent_name}")
        self.current_operation = None
        
    def safe_serialize(self, obj: Any, max_length: int = 200) -> str:
        """Safely serialize objects for logging, preventing crashes"""
        try:
            if obj is None:
                return "None"
            elif isinstance(obj, (str, int, float, bool)):
                result = str(obj)
                return result[:max_length] + "..." if len(result) > max_length else result
            elif isinstance(obj, dict):
                # Only serialize safe keys and truncate values
                safe_dict = {}
                for k, v in list(obj.items())[:5]:  # Limit to first 5 items
                    if isinstance(k, str) and len(k) < 50:
                        safe_dict[k] = self.safe_serialize(v, 50)
                return f"dict({len(obj)} items): {json.dumps(safe_dict, default=str)[:max_length]}"
            elif isinstance(obj, list):
                if len(obj) == 0:
                    return "[]"
                sample = self.safe_serialize(obj[0], 50) if obj else "empty"
                return f"list({len(obj)} items): [{sample}...]"
            else:
                return f"{type(obj).__name__}({str(obj)[:max_length]})"
        except Exception as e:
            return f"<serialization_error: {type(obj).__name__}>"
    
    @contextmanager
    def trace_operation(self, operation: str, **context):
        """Lightweight operation tracing"""
        start_time = time.time()
        operation_id = f"{int(start_time * 1000) % 100000:05d}"  # Simple ID
        
        # Safe context serialization
        safe_context = {k: self.safe_serialize(v, 50) for k, v in context.items()}
        
        try:
            self.current_operation = operation_id
            self.logger.info(f"[START] {self.agent_name}:{operation}:{operation_id} {safe_context}")
            yield operation_id
            
            duration = time.time() - start_time
            self.logger.info(f"[END] {self.agent_name}:{operation}:{operation_id} {duration:.3f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = self.safe_serialize(str(e), 100)
            self.logger.error(f"[ERROR] {self.agent_name}:{operation}:{operation_id} {duration:.3f}s {error_msg}")
            raise
        finally:
            self.current_operation = None
    
    def log_tool_call(self, tool_name: str, args: Dict[str, Any]):
        """Safe tool call logging"""
        try:
            safe_args = self.safe_serialize(args, 150)
            op_id = self.current_operation or "no-op"
            self.logger.info(f"[TOOL] {self.agent_name}:{tool_name}:{op_id} args={safe_args}")
        except Exception:
            # Never let logging break the actual functionality
            pass
    
    def log_tool_result(self, tool_name: str, result: Any):
        """Safe tool result logging"""
        try:
            safe_result = self.safe_serialize(result, 150)
            op_id = self.current_operation or "no-op"
            self.logger.info(f"[RESULT] {self.agent_name}:{tool_name}:{op_id} result={safe_result}")
        except Exception:
            pass

class FilteredMCPToolset(MCPToolset):
    def __init__(self, *args, allowed_tools=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_tools = set(allowed_tools) if allowed_tools else None
        # Optional tracer - won't break if not provided
        self.tracer = None

    def call_tool(self, tool_name, *args, **kwargs):
        # Existing security check (unchanged)
        if self.allowed_tools and tool_name not in self.allowed_tools:
            raise ValueError(f"Tool '{tool_name}' is not allowed for this agent.")
        
        # Optional tracing - won't break existing flow
        if hasattr(self, 'tracer') and self.tracer:
            try:
                call_args = dict(kwargs)
                if args:
                    call_args['_args'] = list(args)
                self.tracer.log_tool_call(tool_name, call_args)
            except Exception:
                pass  # Never let tracing break tool execution
        
        # Call parent method (unchanged)
        try:
            result = super().call_tool(tool_name, *args, **kwargs)
            
            # Optional result logging
            if hasattr(self, 'tracer') and self.tracer:
                try:
                    self.tracer.log_tool_result(tool_name, result)
                except Exception:
                    pass
            
            return result
        except Exception as e:
            # Log error but re-raise unchanged
            if hasattr(self, 'tracer') and self.tracer:
                try:
                    self.tracer.logger.error(f"[TOOL_ERROR] {tool_name}: {str(e)[:100]}")
                except Exception:
                    pass
            raise

class CostLoggingAgent(LlmAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store tracer in __dict__ to avoid Pydantic validation
        try:
            object.__setattr__(self, '_agent_tracer', SafeAgentTracer(self.name))
            # Inject tracer into toolsets if they support it
            for tool in self.tools:
                if isinstance(tool, FilteredMCPToolset):
                    tool.tracer = self._agent_tracer
        except Exception:
            # If tracer setup fails, continue without it
            object.__setattr__(self, '_agent_tracer', None)
    
    @property
    def tracer(self):
        """Property to access the tracer safely"""
        return getattr(self, '_agent_tracer', None)
    
    def _log_cost(self, response):
        # Existing cost logging logic (unchanged)
        usage = getattr(response, "usage", None)
        if usage is None and hasattr(response, "raw_response"):
            usage = getattr(response.raw_response, "usage", None)
        if usage is None and hasattr(response, "response"):
            usage = getattr(response.response, "usage", None)
        if usage is None and isinstance(response, dict):
            usage = response.get("usage", {})
        if usage is None:
            usage = {}
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cost = getattr(response, "cost", None)
        if cost is None:
            cost = usage.get("cost", 0.0)
        model_name = getattr(self.model, "model", None)
        if hasattr(response, "model"):
            model_name = getattr(response, "model", model_name)
        
        # Original logging (unchanged)
        logging.info(
            f"[AGENT COST] Agent={self.name} Model={model_name} "
            f"InputTokens={input_tokens} OutputTokens={output_tokens} Cost=${cost:.6f}"
        )
        
        # Additional trace logging (safe)
        tracer = self.tracer
        if tracer:
            try:
                tracer.logger.info(
                    f"[LLM_COST] {self.name} model={model_name} "
                    f"tokens={input_tokens}→{output_tokens} cost=${cost:.6f}"
                )
            except Exception:
                pass

    async def run_async(self, ctx):
        """Enhanced run method with session tracing"""
        # Add optional tracing to the main agent execution
        tracer = self.tracer
        if tracer:
            try:
                # Extract session ID from context if available
                session_id = getattr(ctx, 'session_id', None) or "unknown"
                
                # Get user query for context
                user_query = ""
                if hasattr(ctx, 'request') and hasattr(ctx.request, 'query'):
                    user_query = ctx.request.query[:100] + "..." if len(ctx.request.query) > 100 else ctx.request.query
                elif hasattr(ctx, 'messages') and ctx.messages:
                    # Try to get the last user message
                    for msg in reversed(ctx.messages):
                        if hasattr(msg, 'content') and msg.content:
                            user_query = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                            break
                
                with tracer.trace_operation("agent_execution", 
                                               session_id=session_id,
                                               query=user_query, 
                                               agent_role=self.name):
                    
                    # Call parent run method
                    async for event in super().run_async(ctx):
                        yield event
            except Exception:
                # If tracing fails, fall back to normal execution
                async for event in super().run_async(ctx):
                    yield event
        else:
            # Normal execution without tracing
            async for event in super().run_async(ctx):
                yield event

# --- Agent Creation ---
def create_domain_agent(name, api_url, allowed_tools=None, instruction=None, model_params=None):
    model_name = AGENT_MODEL_MAP.get(name, REASONING_MODEL)
    params = BASE_MODEL_PARAMS.copy()
    if model_params:
        params.update(model_params)
    tool_objects = []
    if mcp_available and SseServerParams is not None:
        tool_objects.append(
            FilteredMCPToolset(
                connection_params=SseServerParams(
                    url=api_url,
                    timeout=30,
                    sse_read_timeout=60
                ),
                allowed_tools=allowed_tools,
            )
        )
    # Prefix Azure deployment name with 'azure/' if provider is azure
    if provider == "azure":
        model_name = f"azure/{model_name}"
    agent = CostLoggingAgent(
        model=LiteLlm(
            model=model_name,
            **params,
        ),
        name=name,
        instruction=instruction or f"This agent specializes in {name}.",
        tools=tool_objects
    )
    try:
        logger.info(f"[AGENT_CREATE] {name} created with {len(allowed_tools or [])} allowed tools and model {model_name}")
    except Exception:
        pass
    return agent

# --- Agent Configs ---
AGENT_CONFIGS = {
    role: {
        'allowed_tools': AgentPrompts.get_allowed_tools(role),
        'instruction': AgentPrompts.get_instruction(role)
    } for role in AGENT_MODEL_MAP.keys()
}

# --- Build Agents ---
AGENTS = {
    name: create_domain_agent(
        name=name,
        api_url=config.SANATANA_MCP_API_URL,
        allowed_tools=cfg["allowed_tools"],
        instruction=cfg["instruction"],
        model_params=MODEL_PARAMS.get(name)
    )
    for name, cfg in AGENT_CONFIGS.items()
}

root_agent = AGENTS['root_agent']

__all__ = ["AGENTS", "root_agent"]

