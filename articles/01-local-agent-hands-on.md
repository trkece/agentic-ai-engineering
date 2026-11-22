# Building Your First Local AI Agent: From LLM Call to Tool-Using System

*A practical companion to Part 1 of the Agentic AI Engineering series*

An AI agent becomes easier to understand when you build one, run it locally, watch it call tools, and debug the failures yourself.

In this hands-on guide, we will build and run a small customer-support investigation agent using **Python, Ollama, and Qwen3**. The application runs the model locally, exposes three read-only Python functions as tools, and lets the model request those functions as part of a multi-turn interaction.

This is not a production customer-support platform. It is a deliberately small engineering lab for learning the agent execution loop and the responsibilities of the application that hosts it.

**What you will build:** a local assistant that can look up a fictional customer, inspect fictional transaction records, retrieve a support policy, and summarize the evidence. It cannot issue refunds or change accounts.

## 1. Understand the architecture before installing anything

The system has five main pieces:

1. **User interface:** a terminal-based command loop that accepts a request.
2. **Model runtime:** Ollama hosts Qwen3 and exposes a local HTTP API.
3. **Agent harness:** Python sends conversation messages and tool definitions to the model, validates requested tools, executes functions, and returns observations.
4. **Tools:** deterministic Python functions that read the example customer, transaction, and policy data.
5. **Conversation state:** a message list that carries the user request, assistant tool requests, and tool results across model turns.

The interaction looks like this:

```text
User
 |
 v
Python CLI
 |
 v
Agent harness  <-------------------------------+
 |                                              |
 | messages + tool schemas                      | tool observations
 v                                              |
Ollama / Qwen3                                  |
 |                                              |
 | assistant response / tool request            |
 v                                              |
Validate tool name and arguments                 |
 |                                              |
 v                                              |
Execute permitted Python function --------------+
 |
 v
Model produces final response
 |
 v
User
```

The model does not directly execute Python. It produces a structured request describing a tool and its arguments. The host application decides whether that request is permitted, validates it, executes the corresponding function, and sends the result back to the model. This separation is one of the most important concepts in agent engineering.

## 2. Prerequisites

You need:

- macOS for the walkthrough below (the Python project itself is not Mac-specific).
- Python 3.10 or later.
- Ollama installed and running.
- Enough memory and disk space to run the model you select.
- Git installed and access to the public repository.

The example developed for this guide used the Qwen3 8B model variant shown by Ollama as approximately 5.2 GB on disk in that environment. Model tags, quantization, download size, and runtime requirements can change. Check the model library and your machine's available resources before downloading.

Useful official references:

- [Ollama download](https://ollama.com/download)
- [Ollama Qwen3 model library](https://ollama.com/library/qwen3)
- [Ollama Python library](https://github.com/ollama/ollama-python)

## 3. Install and start Ollama on macOS

You can install Ollama using its macOS application or an available package-manager route. This walkthrough uses Homebrew, which was the setup used for the local development session.

```bash
brew install ollama
brew services start ollama
```

Check the service:

```bash
brew services list | grep -i ollama
```

The service should show as started. If you use the Ollama Mac application instead, open the application and let it start the local server. Use one startup method; do not start a second server if one is already listening on the default port.

Ollama's local API normally listens on `http://127.0.0.1:11434`. Check it:

```bash
curl -v http://127.0.0.1:11434/api/tags
```

A successful response contains JSON with a `models` array. An empty array means the server is responding but no model has been downloaded yet.

### Troubleshooting: connection refused

A response like this:

```text
connect to 127.0.0.1 port 11434 failed: Connection refused
```

means that the client reached the local machine but no process accepted the connection on that port. It does not establish that the Python code or model is defective.

Check the Ollama service and start it if needed:

```bash
brew services list | grep -i ollama
brew services start ollama
curl http://127.0.0.1:11434/api/tags
```

If the API is still unavailable, inspect the Ollama application or service logs before reinstalling anything. First isolate whether the server is running, then test the model, then test Python.

## 4. Download and verify Qwen3

Download the model:

```bash
ollama pull qwen3
```

List locally available models:

```bash
ollama list
```

Run a simple model check:

```bash
ollama run qwen3 "Reply with exactly: QWEN3_OK"
```

The expected text is `QWEN3_OK`. This verifies that the model can be invoked through the Ollama CLI. It does not yet verify Python connectivity or tool calling.

Qwen3 supports tool use and thinking capabilities in Ollama. The Python example explicitly sets `think=True` so that the model's thinking mode is enabled for this run. Thinking output and user-facing answer content are separate response fields; the application should display the final answer, not treat internal reasoning as the answer.

## 5. Clone the learning repository

```bash
mkdir -p ~/Projects
cd ~/Projects

git clone https://github.com/trkece/agentic-ai-engineering.git
cd agentic-ai-engineering
```

When you already have the repository locally, update it:

```bash
cd ~/Projects/agentic-ai-engineering
git pull origin main
```

The example lives here:

```text
01-agent-fundamentals/
    customer_support_agent.py
    requirements.txt
    exercises.md
```

## 6. Create an isolated Python environment

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r 01-agent-fundamentals/requirements.txt
```

The repository requires `ollama>=0.5.2`. This minimum version matters because the tool-result message in this example uses the `tool_name` field; the Ollama Python SDK added it in version 0.5.2.

You can check the installed version:

```bash
python -m pip show ollama
```

## 7. Verify each layer before running the agent

Do not debug the entire stack at once. Verify the layers in order.

### Check 1: Ollama API

```bash
curl http://127.0.0.1:11434/api/tags
```

### Check 2: Python SDK connectivity

Activate the virtual environment and run:

```bash
export OLLAMA_HOST=http://127.0.0.1:11434

python - <<'PY'
import os
from ollama import Client

host = os.environ["OLLAMA_HOST"]
client = Client(host=host)

print("Connecting to:", host)
models = [model.model for model in client.list().models]
print("Available models:", models)

assert any(name.startswith("qwen3") for name in models), "Qwen3 is not installed"
print("SUCCESS: Python connected to Ollama and found Qwen3.")
PY
```

Setting `OLLAMA_HOST` explicitly removes ambiguity about which local endpoint the SDK should use. It is not normally required when the default host is correct.

### Check 3: Python model inference

```bash
python - <<'PY'
from ollama import chat

response = chat(
    model="qwen3",
    messages=[
        {"role": "user", "content": "Reply with exactly: PYTHON_QWEN3_WORKING"}
    ],
    think=True,
)

print("Model response:", response.message.content)
PY
```

Only move to the agent test after this request succeeds. If it fails, capture the exception and check the server/API layer before changing the agent code.

## 8. Inspect the tools

The project exposes three read-only functions:

| Tool | Input | Purpose |
|---|---|---|
| `get_customer_details` | `customer_id` | Return a fictional customer record |
| `get_transaction_history` | `customer_id` | Return fictional transaction records |
| `search_support_policy` | `topic` | Retrieve a supported policy |

The tool schemas describe the function name, description, and required arguments. The Python registry maps those public names to actual functions:

```python
TOOL_FUNCTIONS = {
    "get_customer_details": get_customer_details,
    "get_transaction_history": get_transaction_history,
    "search_support_policy": search_support_policy,
}
```

This registry is an allowlist. A model cannot invoke an arbitrary Python function simply by inventing a name.

The execution function performs additional checks:

- The requested name must be in the registry.
- Arguments must be an object.
- The supplied keys must exactly match the tool contract.
- Values must be non-empty strings.
- Only then is the Python function called.

These checks are intentionally simple for the tutorial. Production tool gateways need stronger schema validation, identity and authorization checks, timeouts, rate limits, audit events, and safe error handling.

## 9. Understand the tool-calling loop

The key code path is in `run_agent()`:

```python
response = chat(
    model=MODEL,
    messages=messages,
    tools=TOOLS,
    think=True,
)

assistant_message = response.message
messages.append(assistant_message)

tool_calls = assistant_message.tool_calls or []

if not tool_calls:
    return assistant_message.content or "(The model returned no text.)"

for tool_call in tool_calls:
    name = tool_call.function.name
    arguments = tool_call.function.arguments

    result = execute_tool(name, arguments)

    messages.append({
        "role": "tool",
        "tool_name": name,
        "content": json.dumps(result),
    })
```

The complete implementation wraps this logic in a bounded loop. The process is:

1. Send the conversation and available tool schemas to Qwen3.
2. Receive the assistant message.
3. Inspect whether it contains tool calls.
4. If there are no tool calls, return the final assistant content.
5. For each requested tool, validate its name and arguments.
6. Execute the permitted function.
7. Append the tool result as a tool message.
8. Ask the model to continue with the updated conversation.
9. Stop when the model returns a response without tool calls or the maximum model-turn count is reached.

A single model response can contain more than one tool call. The code therefore iterates through the returned calls. The maximum model-turn limit is not the same as a strict maximum tool-call count: one model turn can request several tools. Production systems should enforce separate budgets for model turns, tool calls, elapsed time, and cost.

The Ollama Python examples and tool-calling documentation demonstrate this pattern: append the assistant message containing tool calls, execute the named function in application code, append each tool result with its tool name, and call the model again.

## 10. Run the agent

Compile-check the Python file:

```bash
python -m py_compile 01-agent-fundamentals/customer_support_agent.py
```

Start the interactive application:

```bash
python 01-agent-fundamentals/customer_support_agent.py
```

The updated CLI supports multi-line prompts. Paste the entire request and type `END` on a line by itself to submit:

```text
> Investigate customer C-1001.
> Retrieve customer details.
> Retrieve transaction history.
> Look up the refund policy.
> Identify pending transactions and explain the findings.
> Do not initiate any refund.
> END
```

This input behavior is deliberate. A basic call to Python's `input()` reads one line only. If a user pastes a multi-line request into a one-line prompt, the remaining lines can be interpreted as separate user messages. That creates confusing results and can make a working agent appear inconsistent. The updated CLI collects lines until the explicit `END` marker.

## 11. What should the agent find?

The data in this repository is fictional and stored in Python dictionaries. For customer `C-1001`, the fixture contains:

| Transaction | Date | Amount | Status |
|---|---|---:|---|
| TX-9001 | 2026-11-18 | $49.99 | Settled |
| TX-9002 | 2026-11-20 | $19.99 | Pending |

The refund policy fixture states that refund requests must be reviewed against the original payment method and eligibility window. The demo cannot issue refunds.

A correct evidence-based summary should distinguish the facts:

- Customer details are returned by the customer lookup tool.
- The transaction history identifies TX-9002 as pending for $19.99.
- The policy requires an eligibility review.
- No refund was executed.
- The fixture does not prove that the pending transaction is eligible for a refund.

The agent should not turn a pending status into an unsupported statement that a refund is due. It should explain what the evidence establishes and what remains unknown.

## 12. Test the behavior deliberately

Run these as separate requests.

### Test A — Customer and transaction investigation

```text
Investigate customer C-1001. Retrieve the customer record, transaction history, and refund policy. Explain the pending transaction and do not initiate a refund.
END
```

Inspect the tool trace. Confirm that the transaction history tool was actually requested and executed. A final answer that mentions a pending transaction is not enough by itself; verify the returned tool result.

### Test B — Unknown customer

```text
Investigate customer C-9999 and explain what the records show.
END
```

Expected: a not-found result. The agent must not invent a customer.

### Test C — Missing identifier

```text
Can you investigate my pending transaction?
END
```

Expected: the agent asks for the customer ID rather than fabricating one.

### Test D — Policy-only request

```text
Explain the account-change policy.
END
```

Expected: the account policy is retrieved and summarized.

### Test E — Unsupported action

```text
Issue a refund for customer C-1001.
END
```

Expected: the assistant explains that this educational demo has no refund-execution tool. It must not claim that a refund was submitted.

Tool selection is model-driven and can vary between runs. Explicitly asking for a tool helps, but it does not guarantee that a model will call it. The execution trace is the evidence. For deterministic application requirements, do not rely on prompt wording alone: orchestrate mandatory data retrieval in trusted application code, then use the model to interpret the collected results.

## 13. Debugging lessons from the local run

The implementation exercise exposed two distinct problems. They are worth understanding because they occur frequently when moving from a notebook demo to a terminal application.

### Problem 1: Connection refused

**Symptom:** the Python application reported a `ConnectionError`, and `curl` could not connect to `127.0.0.1:11434`.

**Diagnosis:** the Ollama API server was not running. The model and Python tool loop had not yet been reached.

**Resolution:** start the Ollama service, then verify the API with `curl`. Only after receiving HTTP 200 should you test model availability and Python inference.

### Problem 2: Multi-line input became separate requests

**Symptom:** a pasted prompt was split into several user inputs. The model asked for a customer ID again because it received only one line in the first request.

**Diagnosis:** the CLI used the one-line `input()` function.

**Resolution:** change the input layer to collect lines until an explicit `END` marker. This is an interface issue, not a model-reasoning issue.

### A disciplined debugging order

Use this sequence:

1. Is the Ollama process running?
2. Does the local API respond?
3. Is the requested model present?
4. Can the Python SDK list models?
5. Can Python run a simple inference request?
6. Does the model return a tool call?
7. Does the application validate and execute the function?
8. Does the tool result return to the model?
9. Does the model produce a final response grounded in the tool output?

Changing prompts, dependencies, and application code simultaneously makes failures harder to isolate. Verify one boundary at a time.

## 14. What this demo does not solve

This project is intentionally limited. It demonstrates the mechanics of a local tool-using agent, not a production service.

Before adapting the pattern to real systems, add:

- **Authentication:** establish the identity of the user and calling service.
- **Authorization:** decide whether that identity may access the requested customer or perform the requested operation. A tool allowlist is not user authorization.
- **Data minimization:** return only the fields needed by the task.
- **Schema validation:** validate types, formats, ranges, and business constraints.
- **Timeouts and budgets:** bound model turns, tool calls, wall-clock time, tokens, and retries independently.
- **Idempotency:** make retry behavior safe for operations that can change state.
- **Human approval:** gate financial, sensitive, irreversible, or high-impact actions.
- **Observability:** capture correlation IDs, model and prompt versions, tool names, validated inputs, outcomes, durations, and approval events while protecting sensitive data.
- **Evaluation:** test tool selection, argument correctness, policy compliance, groundedness, failure recovery, latency, and cost.
- **Security controls:** defend against prompt injection, data exfiltration, excessive agency, and unsafe tool composition.

Do not add a write-capable refund function merely to make the demo appear more autonomous. First build the approval, authorization, idempotency, audit, and recovery controls around it.

## 15. What you should understand after completing the lab

By the end of this exercise, you should be able to explain:

1. Why an LLM call is not, by itself, a complete agent.
2. Why the application—not the model—executes tool functions.
3. How tool schemas describe callable capabilities.
4. Why tool requests require allowlisting and argument validation.
5. How assistant tool calls and tool results become part of the conversation.
6. Why model-turn limits and tool-call limits are different.
7. Why local API connectivity should be checked before debugging model behavior.
8. Why a final answer must be checked against actual tool results.

## Repository and source code

The complete implementation, dependency file, and exercises are maintained here:

- [Agentic AI Engineering repository](https://github.com/trkece/agentic-ai-engineering)
- [Python customer-support agent](https://github.com/trkece/agentic-ai-engineering/blob/main/01-agent-fundamentals/customer_support_agent.py)
- [Part 1 — Agent Fundamentals](https://github.com/trkece/agentic-ai-engineering/blob/main/articles/01-agent-fundamentals.md)
- [Hands-on exercises](https://github.com/trkece/agentic-ai-engineering/blob/main/01-agent-fundamentals/exercises.md)

## Verification note

During development, the local Ollama API was initially unavailable and returned connection refused. Starting the Ollama service resolved that issue; the API then returned HTTP 200 and listed the Qwen3 model. Python inference also succeeded, and the observed run executed the customer-details and refund-policy tools.

The transaction-history tool still needs to be observed in a single complete request using the updated multi-line CLI. The expected transaction values above come from the checked-in fictional fixture data; they should not be mistaken for a fully observed three-tool runtime trace. This distinction between expected behavior and verified behavior is part of responsible engineering documentation.

## Next article

**Tool Calling and Function Execution: How AI Agents Interact with APIs, Databases, and Enterprise Systems.**

We will go deeper into typed tool contracts, schema design, routing, authorization, read-versus-write boundaries, retries, timeouts, idempotency, audit trails, and safe failure recovery.
