from pickle import load

agent = None

with open("<<ARCHIVED_AGENTS_PATH>>", "rb") as file:
    agent = load(file)

print(" + Set breakpoint here! + ")
