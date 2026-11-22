# Agentic AI Engineering

A practical, implementation-first learning series for designing, building, evaluating, and operating AI agents—from first principles to enterprise-grade systems.

The material is intended for AI/ML engineers, software engineers, data scientists, architects, technical product leaders, and technology leaders.

## Learning path

| Part | Topic | Status |
|---|---|---|
| 01 | Agent fundamentals: concepts, architecture, and your first agent | Available |
| 02 | Tool calling and function execution: APIs, databases, and enterprise systems | Planned |
| 03 | State, context engineering, and memory | Planned |
| 04 | Planning, workflows, and multi-agent orchestration | Planned |
| 05 | Retrieval, knowledge graphs, and enterprise context | Planned |
| 06 | Evaluation, observability, safety, and governance | Planned |
| 07 | Production architecture and deployment patterns | Planned |

## Start here

1. Read [Part 1 — Agent Fundamentals](articles/01-agent-fundamentals.md).
2. Run the [customer-support agent example](01-agent-fundamentals/).
3. Work through the [exercises](01-agent-fundamentals/exercises.md).

## Quick start

Requirements: Python 3.10+ and [Ollama](https://ollama.com/).

```bash
ollama pull qwen3
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r 01-agent-fundamentals/requirements.txt
python 01-agent-fundamentals/customer_support_agent.py
```

The example uses fictional, in-memory records and read-only tools. It does not connect to a real CRM, payment platform, or customer database. Model behavior and tool selection can vary between runs.

### Entering multi-line prompts

The CLI accepts multi-line requests. Paste your full prompt, then type `END` on a separate line to submit it. Type `EXIT` or `QUIT` on the first line to close the application. For example:

```text
> Investigate customer C-1001.
> Retrieve customer details and transaction history.
> Explain pending transactions and the refund policy.
> Do not initiate a refund.
> END
```


## Design principles

- Make autonomy explicit and bounded.
- Treat tool calls as untrusted requests that require validation.
- Separate model reasoning from deterministic application logic.
- Enforce authorization outside the model.
- Add timeouts, observability, evaluation, and human approval before production use.
- Prefer the simplest architecture that satisfies the use case.

## Repository structure

```text
articles/                         Long-form learning articles
01-agent-fundamentals/             Part 1 runnable example and exercises
```

## Contributing

Issues and pull requests with corrections, examples, and improvements are welcome. Please avoid including secrets, credentials, or real customer data.

## Disclaimer

This repository is educational material, not production-ready software or legal, security, or compliance advice.
