import asyncio
from arcanis_brain import ArcanisBrain, BrainConfig


async def main():
    config = BrainConfig(
        storage_path="~/.arcanis/brain",
        safety_mode="strict",
        memory_ttl_seconds=1800,
    )

    brain = ArcanisBrain(config)
    await brain.initialize()

    print("ArcanisBrain initialized. Send a message to test.")

    response = await brain.process("Hello! What can you help me with?")
    print(f"Response: {response}")

    response = await brain.process("Can you help me write a Python function to calculate fibonacci?")
    print(f"Response: {response}")

    print("\n-- Agent Registry --")
    for agent in brain.agents.registry.list():
        print(f"  Agent: {agent.name} ({agent.role})")

    print("\n-- Audit Log --")
    for entry in brain.security.audit.get_recent():
        print(f"  [{entry['event_type']}] {entry.get('action', '')}")

    await brain.shutdown()
    print("\nArcanisBrain shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
