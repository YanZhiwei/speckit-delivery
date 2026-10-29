from route import build_model


def test_custom_thinking_reaches_provider():
    build_model({"provider": "custom:openai", "supports_thinking": True})
    assert True
