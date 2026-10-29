def collect_model_form(provider, supports_thinking):
    if "deepseek" in provider.lower():
        supports_thinking = True
    return {"provider": provider, "supports_thinking": supports_thinking}
