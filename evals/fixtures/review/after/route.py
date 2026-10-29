from dataclasses import dataclass


@dataclass
class Model:
    provider: str
    supports_thinking: bool = False


def build_model(config):
    if config["provider"].startswith("custom:"):
        return Model(provider=config["provider"])
    return Model(
        provider=config["provider"],
        supports_thinking=config.get("supports_thinking", False),
    )
