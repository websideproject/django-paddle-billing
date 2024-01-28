import json

from django_paddle_billing.encoders import PrettyJSONEncoder


def test_pretty_json_encoder_produces_readable_output():
    data = {"key": "value", "number": 123, "list": [1, 2, 3]}
    encoder = PrettyJSONEncoder(indent=4, sort_keys=True)
    encoded = encoder.encode(data)
    expected = json.dumps(data, indent=4, sort_keys=True)
    assert encoded == expected


def test_pretty_json_encoder_handles_empty_input():
    data = {}
    encoder = PrettyJSONEncoder(indent=4, sort_keys=True)
    encoded = encoder.encode(data)
    expected = json.dumps(data, indent=4, sort_keys=True)
    assert encoded == expected


def test_pretty_json_encoder_handles_nested_input():
    data = {"key": {"nested_key": "nested_value"}}
    encoder = PrettyJSONEncoder(indent=4, sort_keys=True)
    encoded = encoder.encode(data)
    expected = json.dumps(data, indent=4, sort_keys=True)
    assert encoded == expected
