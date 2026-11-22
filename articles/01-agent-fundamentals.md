# Agentic AI: From Fundamentals to Enterprise-Grade Systems

## Part 1 — Understanding, Designing, and Building Your First AI Agent

An AI agent is not simply a language model with a sophisticated prompt. It is a software system in which a model can interpret a goal, select from a set of permitted actions, observe the results, and continue until it reaches a stopping condition.

That distinction matters. The engineering challenge is not just generating a plausible answer. It is controlling a system that can take actions, interact with external state, and potentially create real-world consequences.

This article builds a foundation from first principles and then implements a small, local, tool-using agent.

## 1. The progression: from LLM calls to agents

A useful way to understand the space is as a progression in system capability:

1. **LLM call:** provide input, receive generated output. The application controls the sequence.
2. **LLM with retrieval or tools:** the model can use supplied context or request a defined tool, but the overall workflow may remain fixed.
3. **Workflow:** application code coordinates a known sequence of steps, branches, and integrations. The model may power individual steps.
4. **Agent:** the model can choose among permitted actions and determine the next step based on observations, within explicit boundaries.

These are not rigid product categories. A system may combine deterministic workflows with agentic decisions. In enterprise environments, that hybrid is often preferable: use code for predictable control flow and an agent for decisions that genuinely benefit from flexible interpretation.

The word *agent* should describe an architectural property, not serve as a marketing label for every application that calls an LLM.

## 2. What makes a system an agent?

An agent typically has the following elements:

- **Goal or task:** what outcome it is trying to achieve.
- **Model:** interprets context and proposes a next action.
- **Instructions and policies:** define role, constraints, and permitted behavior.
- **Tools:** typed interfaces to capabilities such as searching records or invoking an API.
- **Context:** information needed to make the current decision.
- **State:** information about the current execution, completed steps, and pending work.
- **Execution harness:** application code that invokes the model, validates tool requests, executes tools, and returns observations.
- **Stopping conditions:** success, failure, approval required, or a bounded execution limit.
- **Observability and evaluation:** evidence of what happened and whether the outcome was correct.

A model alone is not the complete agent. The harness and the surrounding controls are part of the system.

## 3. The agent loop

A simplified agent loop looks like this:

```text
             ┌─────────────────────┐
             │ Goal + Context      │
             └──────────┬──────────┘
                        v
             ┌─────────────────────┐
             │ Model selects next  │
             │ action or response  │
             └──────────┬──────────┘
                        v
             ┌─────────────────────┐
             │ Validate request    │
             │ and permissions     │
             └──────────┬──────────┘
                        v
             ┌─────────────────────┐
             │ Execute permitted   │
             │ tool                │
             └──────────┬──────────┘
                        v
             ┌─────────────────────┐
             │ Return observation  │
             │ to model            │
             └──────────┬──────────┘
                        v
                Continue or stop
```

The conceptual cycle is **reason → act → observe → adapt**. In a real implementation, the model's proposed action is not executed blindly. The application validates the tool name, arguments, identity, permissions, and execution policy first.

A stopping condition is essential. Without one, an agent can loop, waste tokens, repeat actions, or continue after it should have stopped.

## 4. Tool calling: the boundary between language and software

A tool is a function exposed to the model through a structured schema. For example:

- `get_customer_details(customer_id)`
- `get_transaction_history(customer_id)`
- `search_support_policy(topic)`

The schema tells the model what a tool is called, what it does, and which arguments it accepts. The model can request a tool call, but the host application executes the actual function.

This separation is fundamental:

- The model proposes.
- The application validates.
- The tool implementation executes.
- The result is returned as an observation.

Never treat a model-generated tool request as proof that the caller is authorized. Authentication and authorization must be enforced by trusted application services, not by prompt instructions.

## 5. A practical implementation

The companion example in [customer_support_agent.py](../01-agent-fundamentals/customer_support_agent.py) uses:

- Python
- Ollama running locally
- Qwen3 as the language model
- Fictional customer, transaction, and policy records
- Three read-only tools
- A bounded execution loop

### Execution flow

1. The user asks for help with a customer issue.
2. The application sends the conversation and tool definitions to the model.
3. The model may request one or more tools.
4. The application checks each requested tool against an allowlist and validates its arguments.
5. The application executes the tool and appends its result to the conversation.
6. The model receives the observations and either requests another action or returns a final response.
7. The loop stops when the model responds without tool calls or the configured turn limit is reached.

Tool selection is probabilistic. A model may choose a different sequence, ask for clarification, or answer without using every available tool. Any displayed trace should therefore be understood as illustrative rather than guaranteed.

### Run it

Install Ollama and pull the model:

```bash
ollama pull qwen3
```

Then install the Python dependency and run the example:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r 01-agent-fundamentals/requirements.txt
python 01-agent-fundamentals/customer_support_agent.py
```

The program uses mock data. It does not access real customer accounts or perform transactions.

## 6. Understand the autonomy spectrum

Autonomy is not binary. A practical classification is:

| Level | Pattern | Example |
|---|---|---|
| 0 | Model response only | Draft an answer |
| 1 | Model selects read-only tools | Look up customer and policy information |
| 2 | Model coordinates multiple steps | Gather evidence and prepare a recommendation |
| 3 | Model proposes consequential actions; human approves | Prepare a refund request for approval |
| 4 | Bounded execution of approved actions | Execute a low-risk action within strict policy limits |
| 5 | Broad delegated autonomy | Open-ended operation across systems |

The higher the autonomy, the more demanding the requirements for identity, authorization, policy enforcement, auditability, rollback, monitoring, and human oversight become.

Most enterprise use cases should begin with read-only or human-approved actions. Increase autonomy only when evidence demonstrates that the system is reliable and the risk is acceptable.

## 7. Context, state, and memory are different

These terms are often used interchangeably, but they solve different problems.

- **Context** is the information available to the model for its current decision: instructions, user input, retrieved documents, and recent observations.
- **State** is the structured record of the execution: current task status, completed steps, pending approvals, and intermediate results.
- **Memory** is information retained for use beyond the immediate model call or task, subject to relevance, permissions, retention, and privacy policies.

A conversation history is not automatically a reliable memory system. Durable memory needs explicit decisions about what is stored, who can access it, how it is updated, and when it expires.

## 8. Production engineering: what the demo leaves out

A local demonstration is useful for learning the control loop. It is not a production architecture.

Before deploying an agent, design for:

### Identity and authorization
Authenticate the user and service. Authorize every operation at the tool or service boundary. Scope access to the minimum required data.

### Input and argument validation
Validate types, formats, ranges, and business constraints. Reject unknown tools and unexpected arguments. Treat retrieved content and model output as untrusted data.

### Bounded execution
Set limits for model turns, tool calls, wall-clock time, token consumption, and retries. Define explicit terminal states.

### Reliability
Use timeouts, controlled retries, idempotency keys for write operations, and clear handling of partial failure. Do not blindly retry a non-idempotent operation.

### Human oversight
Require approval for sensitive, irreversible, financial, legal, or otherwise consequential actions. Make the proposed action and its evidence visible to the approver.

### Observability
Record correlation IDs, model and prompt versions, tool name, validated arguments, execution duration, outcome, and approval events. Protect logs from leaking sensitive data.

### Evaluation
Test task completion, tool-selection accuracy, argument correctness, policy compliance, latency, cost, and failure recovery. Include adversarial and out-of-distribution cases. Evaluate the full system, not only the model's final text.

### Security
Consider prompt injection, data exfiltration, excessive agency, insecure tool design, and confused-deputy risks. Retrieved documents and tool outputs must not be allowed to override trusted system policy.

## 9. Common architectural patterns

- **ReAct-style loop:** interleave model decisions with tool observations.
- **Plan-and-execute:** create a plan, then execute steps with checks and replanning as needed.
- **Deterministic workflow with agentic steps:** keep orchestration in code and delegate bounded decisions to the model.
- **Human-in-the-loop:** pause execution for approval or clarification.
- **Multi-agent collaboration:** separate responsibilities across agents, with explicit contracts and coordination. Multiple agents are not automatically better; they add communication, state, evaluation, and failure complexity.

Choose a pattern based on task uncertainty, risk, latency, cost, and the need for control—not because a framework makes it fashionable.

## 10. Frameworks and protocols to explore

The example deliberately uses a small custom harness so the underlying mechanics remain visible. After understanding those mechanics, explore:

- [LangGraph](https://langchain-ai.github.io/langgraph/) — graph-based orchestration, state, and control flow.
- [LlamaIndex](https://docs.llamaindex.ai/) — data and retrieval-oriented application patterns, including agents.
- [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/) — Microsoft's agent and workflow development ecosystem.
- [CrewAI](https://docs.crewai.com/) — role-oriented agent collaboration and crews.
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) — a protocol for connecting AI applications to external tools and context providers.

Frameworks can accelerate implementation, but they do not remove the need to understand tool contracts, security, state, evaluation, and operational controls.

## 11. Exercises

See [exercises.md](../01-agent-fundamentals/exercises.md). Start by tracing the execution loop, then add validation and failure handling before attempting any write-capable tool.

## 12. Key takeaways

1. An agent is a system, not merely a prompt or an LLM API call.
2. The execution harness is responsible for validation, permissions, tool execution, and stopping conditions.
3. Tool calls are requests, not authorization.
4. Context, state, and memory have distinct roles.
5. Autonomy should be deliberately bounded and increased only with evidence.
6. Production readiness requires security, observability, evaluation, and failure handling from the beginning.

## What comes next?

**Part 2 — Tool Calling and Function Execution: How Agents Interact with APIs, Databases, and Enterprise Systems.**

We will extend the same codebase and examine typed tool contracts, schema validation, routing, authentication, authorization, retries, timeouts, idempotency, audit trails, and safe handling of read versus write operations.
