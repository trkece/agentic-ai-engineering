# Part 1 Exercises — Agent Fundamentals

Use the local demo and fictional records in this directory. Do not connect real customer data or credentials.

## Exercise 1: Trace the agent loop

Run the example with:

> Investigate customer C-1001 and explain the pending transaction.

Record:
- The model's first response.
- Which tools it requests.
- The arguments passed to each tool.
- The observations returned.
- Whether it makes another model turn before answering.

Repeat the same prompt. Did the model choose exactly the same tool sequence? Why might the trace vary?

## Exercise 2: Test missing and unknown identifiers

Try a known ID, an unknown ID, and a prompt without a customer ID.

Expected behavior:
- The tools must not invent records.
- Unknown IDs should return a not-found result.
- The agent should ask for missing information rather than fabricate it.

## Exercise 3: Add a new read-only tool

Add `get_order_status(order_id: str)`.

Tasks:
1. Create a deterministic Python function backed by fictional in-memory data.
2. Add a JSON tool schema.
3. Register the function in the allowlist.
4. Add exact argument validation.
5. Test known and unknown order IDs.

## Exercise 4: Add a stricter execution budget

The current demo limits model turns. Extend it to track:
- Total tool calls.
- Total elapsed time.
- Maximum calls per tool.
- A clear stop reason.

Explain why a model-turn limit and a tool-call limit are different controls.

## Exercise 5: Introduce structured state

Create a task-state object that records:
- Task ID.
- Customer ID, if known.
- Tools already called.
- Evidence collected.
- Current status.
- Stop reason.

Keep this state in application code rather than asking the model to be the sole source of truth.

## Exercise 6: Threat-model the example

Identify at least five risks if the read-only tools were replaced with tools that could issue refunds or change customer accounts.

For each risk, propose a control. Consider authorization, approval, idempotency, audit logging, prompt injection, and partial failure.

## Completion criteria

You should be able to explain the distinction between:
- A model-generated tool request and an executed tool.
- A tool allowlist and user authorization.
- Context and application state.
- A model turn limit and a tool-call limit.
- A successful model response and a verified business outcome.
