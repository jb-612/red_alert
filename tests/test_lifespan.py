"""Tests for lifespan context manager replacing deprecated startup event (WI-5.1)."""

import ast
import importlib


def test_no_on_event_in_main():
    """main.py should not use @app.on_event (deprecated). Use lifespan instead."""
    spec = importlib.util.find_spec("backend.main")
    assert spec is not None
    assert spec.origin is not None

    with open(spec.origin) as f:
        source = f.read()

    tree = ast.parse(source)

    # Walk AST looking for app.on_event decorator calls
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    assert decorator.func.attr != "on_event", (
                        "Found deprecated @app.on_event decorator in main.py. "
                        "Use lifespan context manager instead."
                    )


def test_lifespan_function_exists():
    """main.py should define a lifespan async context manager."""
    from backend.main import lifespan

    assert callable(lifespan)


def test_app_has_lifespan():
    """The FastAPI app should be configured with a lifespan."""
    from backend.main import app

    # FastAPI stores lifespan handler on the router
    assert app.router.lifespan_context is not None


def test_health_endpoint_works(client):
    """Health endpoint should work with the lifespan-based app."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
