"""A small, read-only tool-using agent for learning.

Requirements:
    Python 3.10+
    Ollama installed and running
    ollama pull qwen3
    pip install -r 01-agent-fundamentals/requirements.txt

All records below are fictional and held in memory. This is an educational
example, not a production customer-support integration.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from ollama import chat


MODEL = "qwen3"
MAX_MODEL_TURNS = 6

CUSTOMERS = {
    "C-1001": {
        "name": "Avery Morgan",
        "tier": "Gold",
        "email": "avery@example.test",
        "status": "Active",
    },
    "C-1002": {
        "name": "Jordan Lee",
        "tier": "Standard",
        "email": "jordan@example.test",
        "status": "Active",
    },
}

TRANSACTIONS = {
    "C-1001": [
        {"id": "TX-9001", "date": "2026-11-18", "amount": 49.99, "status": "Settled"},
        {"id": "TX-9002", "date": "2026-11-20", "amount": 19.99, "status": "Pending"},
    ],
    "C-1002": [
        {"id": "TX-9010", "date": "2026-11-19", "amount": 12.50, "status": "Settled"},
    ],
}

POLICIES = {
    "refund": (
        "Refund requests must be reviewed against the original payment method "
        "and eligibility window. This demo cannot issue refunds."
    ),
    "delivery": (
        "For a delayed delivery, verify the order status and estimated delivery "
        "date before communicating an updated expectation."
    ),
    "account": (
        "Account changes require identity verification through an approved "
        "authentication workflow. This demo cannot change account details."
    ),
}


def get_customer_details(customer_id: str) -> dict[str, Any]:
    """Return a fictional customer record for a known customer ID."""
    if customer_id not in CUSTOMERS:
        return {"found": False, "message": "Customer not found."}
    return {"found": True, "customer": CUSTOMERS[customer_id]}


def get_transaction_history(customer_id: str) -> dict[str, Any]:
    """Return transactions only when the customer exists in the demo data."""
    if customer_id not in CUSTOMERS:
        return {"found": False, "message": "Customer not found."}
    return {"found": True, "transactions": TRANSACTIONS.get(customer_id, [])}


def search_support_policy(topic: str) -> dict[str, Any]:
    """Find a small set of supported policy topics."""
    normalized = topic.strip().lower()
    if not normalized:
        return {"found": False, "message": "A policy topic is required."}
    policy = POLICIES.get(normalized)
    if policy is None:
        return {
            "found": False,
            "supported_topics": sorted(POLICIES),
            "message": "No exact policy topic found.",
        }
    return {"found": True, "topic": normalized, "policy": policy}


TOOL_FUNCTIONS: dict[str, Callable[..., dict[str, Any]]] = {
    "get_customer_details": get_customer_details,
    "get_transaction_history": get_transaction_history,
    "search_support_policy": search_support_policy,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_details",
            "description": "Look up a fictional customer by customer ID.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transaction_history",
            "description": "Read the transaction history for a known customer ID.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_support_policy",
            "description": "Look up a support policy topic: refund, delivery, or account.",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"],
            },
        },
    },
]

SYSTEM_PROMPT = """
You are a customer-support investigation assistant in an educational demo.
Use the available read-only tools when they help answer the user's question.
Never claim that you issued a refund, changed an account, or performed an action
that the tools cannot perform. Distinguish verified tool results from assumptions.
If a customer ID is missing, ask the user for it. Do not invent customer records.
The records are fictional. Keep the answer concise and explain relevant evidence.
""".strip()


def execute_tool(name: str, arguments: Any) -> dict[str, Any]:
    """Validate the tool name and basic argument shape before execution."""
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        return {"ok": False, "error": f"Tool '{name}' is not permitted."}

    if not isinstance(arguments, dict):
        return {"ok": False, "error": "Tool arguments must be an object."}

    expected_arguments = {
        "get_customer_details": {"customer_id"},
        "get_transaction_history": {"customer_id"},
        "search_support_policy": {"topic"},
    }[name]

    if set(arguments) != expected_arguments:
        return {
            "ok": False,
            "error": "Arguments do not match the tool contract.",
            "expected_arguments": sorted(expected_arguments),
        }

    if any(not isinstance(value, str) or not value.strip()
           for value in arguments.values()):
        return {"ok": False, "error": "All tool arguments must be non-empty strings."}

    try:
        return {"ok": True, "result": function(**arguments)}
    except (TypeError, ValueError) as exc:
        # In production, log a sanitized error with a correlation ID.
        return {"ok": False, "error": f"Tool input error: {type(exc).__name__}"}


def run_agent(user_question: str) -> str:
    """Run a bounded model/tool loop and return the final assistant text."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_question},
    ]

    for turn in range(1, MAX_MODEL_TURNS + 1):
        response = chat(model=MODEL, messages=messages, tools=TOOLS, think=True)
        assistant_message = response.message
        messages.append(assistant_message)

        tool_calls = assistant_message.tool_calls or []
        if not tool_calls:
            return assistant_message.content or "(The model returned no text.)"

        for tool_call in tool_calls:
            name = tool_call.function.name
            arguments = tool_call.function.arguments

            print(f"\n[turn {turn}] requested tool: {name}")
            print(f"[turn {turn}] arguments: {json.dumps(arguments, default=str)}")

            result = execute_tool(name, arguments)
            print(f"[turn {turn}] tool result: {json.dumps(result, default=str)}")

            messages.append(
                {
                    "role": "tool",
                    "tool_name": name,
                    "content": json.dumps(result, default=str),
                }
            )

    return (
        "Execution stopped because the maximum number of model turns was reached. "
        "The task may be incomplete; review the tool trace before taking action."
    )


def read_multiline_question() -> str | None:
    """Read a complete request until END; return None when the user exits."""
    print("Paste your request. Type END on a line by itself to submit.")
    print("Type EXIT on the first line to quit.")

    lines: list[str] = []
    while True:
        try:
            line = input("> ")
        except EOFError:
            # Treat Ctrl-D as submission when text has been entered.
            return "\n".join(lines).strip() if lines else None
        except KeyboardInterrupt:
            print("\nInput cancelled.")
            return ""

        command = line.strip().upper()
        if command == "END":
            return "\n".join(lines).strip()
        if command in {"EXIT", "QUIT"} and not lines:
            return None

        lines.append(line)


def main() -> None:
    print("Customer Support Investigation Agent (local educational demo)")
    print("Try investigating customer C-1001 and its pending transaction.")
    print("Multi-line input is supported; submit each request with END.\n")

    while True:
        question = read_multiline_question()

        if question is None:
            print("Goodbye.")
            break
        if not question:
            continue

        try:
            answer = run_agent(question)
            print(f"\nAgent: {answer}\n")
        except Exception as exc:
            # Keep the user-facing error generic; production systems should
            # emit structured, sanitized diagnostics to protected logs.
            print(
                "\nAgent: The request could not be completed. "
                f"Error type: {type(exc).__name__}. "
                "Check that Ollama is running and the model is available.\n"
            )


if __name__ == "__main__":
    main()
