"""Tests for sandbox_app."""

import json

from sandbox_app import greet, main


def test_greet() -> None:
    assert greet("agent") == "Hello, agent!"


def test_main_json_output(capsys) -> None:
    rc = main(["--name", "fixture", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["message"] == "Hello, fixture!"
    assert data["app"] == "sandbox-app"
