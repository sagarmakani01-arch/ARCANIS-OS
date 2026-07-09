# Agents Module

Multi-agent orchestration framework.

## AgentRegistry

Central registry for agent identities. Supports registration, lookup by capability, and tool-based selection.

## AgentCommunicator

Message-passing system between agents with send, receive, and broadcast capabilities.

## TaskDelegator

Assigns tasks to agents with permission checks, execution tracking, and result collection.

## ToolRegistry

Extensible tool system with built-in tools (reason, memory, search, analyze, compose, generation, computation, retrieval) and support for custom tool registration.
