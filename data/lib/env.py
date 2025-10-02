def __getattr__(name):
    return env[name]

env = {}