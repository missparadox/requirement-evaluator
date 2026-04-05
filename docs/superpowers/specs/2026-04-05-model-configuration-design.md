# Model Configuration Design

## Overview

This document defines the first model configuration design for the requirements evaluator backend.

The current backend already supports a configurable OpenAI-backed path and a static fallback path. This design expands that capability into a deterministic provider selection flow with four runtime modes:

1. OpenAI
2. Zhipu
3. Codex CLI
4. Debug fallback

The selection order is fixed. The backend must evaluate the providers in that order and choose the first available option. The frontend remains unchanged.

## Goals

This design must:
- keep model configuration fully in backend environment variables
- add deterministic provider priority and startup behavior
- support OpenAI with configurable API key, model, and base URL
- support Zhipu with configurable API key, model, and base URL
- support Codex CLI execution when the local `codex` binary is available
- preserve a static fallback path for explicit debug use only
- fail fast with a clear startup error when no runtime mode is available

## Non-Goals

This design must not include:
- frontend model selection
- admin configuration pages
- runtime provider switching from the browser
- multi-provider fan-out or A/B execution
- secret storage beyond environment variables

## Runtime Modes

### Priority Order

The backend must resolve the model provider in this exact order:

1. OpenAI
2. Zhipu
3. Codex CLI
4. Debug fallback

The first satisfied condition wins. Lower-priority providers must not be considered once a higher-priority provider is available.

### Mode 1: OpenAI

OpenAI is selected when `OPENAI_API_KEY` is present and not blank.

Configuration:
- `OPENAI_API_KEY`
- `OPENAI_MODEL`, default `gpt-5.4`
- `OPENAI_BASE_URL`, default OpenAI-compatible base URL for the Responses API

Behavior:
- the backend builds an OpenAI client using the configured base URL
- the backend calls the Responses API
- metadata stores `model_provider = "openai"` and the resolved model name

### Mode 2: Zhipu

Zhipu is selected when OpenAI is unavailable and `ZHIPU_API_KEY` is present and not blank.

Configuration:
- `ZHIPU_API_KEY`
- `ZHIPU_MODEL`, default `glm-5`
- `ZHIPU_BASE_URL`, default Zhipu-compatible API base URL

Behavior:
- the backend builds an OpenAI-compatible client using Zhipu credentials and base URL
- the same report-generation contract is used as OpenAI
- metadata stores `model_provider = "zhipu"` and the resolved model name

### Mode 3: Codex CLI

Codex CLI is selected when OpenAI and Zhipu are unavailable and the local `codex` executable is discoverable on `PATH`.

Configuration:
- `CODEX_MODEL`, default `gpt-5.4`

Behavior:
- the backend invokes `codex exec` in non-interactive mode
- the backend passes one combined prompt containing:
  - the skill text
  - the report template text
  - the generated packet text
- the backend passes `--model <resolved_model_name>`
- authentication relies on the local Codex login state already present on the machine
- stdout is treated as the final Markdown report
- non-zero exit, timeout, or empty stdout is treated as evaluation failure
- metadata stores `model_provider = "codex"` and the resolved model name

### Mode 4: Debug Fallback

Debug fallback is selected only when OpenAI, Zhipu, and Codex CLI are all unavailable and `REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK=1`.

Behavior:
- the backend uses the static fallback client
- metadata stores `model_provider = "static"`
- this path is for local debugging only and is not considered a production mode

## Provider Resolution Rules

Provider resolution must normalize environment variables before use.

Normalization rules:
- missing values are treated as missing
- empty strings are treated as missing
- strings containing only whitespace are treated as missing
- model values fall back to their documented defaults after normalization
- debug fallback is enabled only by the exact string `1`

The backend must expose one provider-resolution function that returns:
- selected provider name
- resolved model name
- resolved base URL when relevant
- enough credential/configuration data to construct the client

## Startup Behavior

The backend must fail fast during startup if none of the four runtime modes is available.

Startup failure conditions:
- `OPENAI_API_KEY` is missing or blank
- `ZHIPU_API_KEY` is missing or blank
- `codex` is not found on `PATH`
- `REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK` is not `1`

When startup fails, the error message must clearly explain:
- that no model provider is available
- the provider priority order
- which enabling condition was checked for each provider
- that `REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK=1` can be used for local debugging

The backend must not wait until the first evaluation request to surface this error.

## Backend Structure

### Settings Layer

`backend/app/core/config.py` should expand from a single `model_name` field into provider-specific configuration.

Settings should include:
- data directory
- OpenAI API key, model, and base URL
- Zhipu API key, model, and base URL
- Codex model
- debug fallback flag

Settings should also expose normalized helper accessors where useful so the rest of the backend does not need to repeat blank-string checks.

### Model Client Layer

`backend/app/clients/model_client.py` should be responsible for:
- provider resolution by priority
- client construction for the selected provider
- reporting the selected provider name

The model client layer should introduce these concrete clients:
- `OpenAIModelClient`
- `CodexModelClient`
- `StaticModelClient`

Zhipu may reuse `OpenAIModelClient` with different credentials and base URL rather than adding a separate transport implementation.

### API Layer

The existing API shape does not change.

The API layer continues to:
- create evaluations
- run background jobs
- expose detail status and metadata

The only functional change visible through the API is that `model_provider` and `model_name` may now reflect `openai`, `zhipu`, `codex`, or `static`.

## Codex Execution Contract

The Codex execution path must remain minimal and deterministic.

Command shape:
- `codex exec <prompt>`
- `--model <resolved_model_name>`

Execution rules:
- run non-interactively
- capture stdout and stderr
- treat stdout as the final Markdown report body
- trim surrounding whitespace before validating emptiness
- if the process exits non-zero, raise a runtime error that includes stderr context
- if stdout is empty after trimming, raise a runtime error

The backend should not depend on interactive Codex features, session resumption, or browser flows.

## Testing

The backend test suite must cover:
- OpenAI selected when `OPENAI_API_KEY` is configured
- Zhipu selected when OpenAI is unavailable and `ZHIPU_API_KEY` is configured
- Codex selected when API-key-based providers are unavailable and `codex` exists
- debug fallback selected only when higher-priority modes are unavailable and the debug flag is `1`
- startup failure when none of the four modes is available
- blank environment values do not count as configured credentials
- resolved `model_provider` and `model_name` are persisted in evaluation metadata

Codex tests should mock executable discovery and subprocess execution rather than shelling out to the real binary.

## Rollout Notes

This design keeps the first release operationally simple:
- users control model behavior with environment variables only
- OpenAI remains the primary production path
- Zhipu provides a second hosted-provider path
- Codex provides a local machine execution path when API-key-based providers are unavailable
- static fallback remains explicit and debug-only

This is sufficient for the first release and leaves room for future provider expansion without requiring frontend changes.
