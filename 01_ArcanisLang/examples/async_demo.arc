# Async programming in ArcanisLang
# WARNING: Async is experimental in v0.1.0

async fun fetch_data(url):
    return "Data from " + url

# Note: Full async runtime is under development
print("Async support is experimental in ArcanisLang v0.1.0")
print("Use async fun for defining asynchronous functions")

async fun simulate_task(name, duration):
    sleep(duration)
    return "Task '" + name + "' completed"

# For now, sync wrappers are recommended:
fun fetch(url):
    return "Response from " + url

print(fetch("https://arcanis.dev"))
