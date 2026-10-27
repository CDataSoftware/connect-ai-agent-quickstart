"""Against a real Connect AI account. Opt in:

    set -a; source .env; set +a
    RUN_LIVE_TESTS=1 pytest -m live

Needs CDATA_USERNAME and CDATA_PAT. No LLM is called.
These pin down behaviour discovered by hand, so a Connect AI or connector
change that breaks the demo's assumptions shows up here.
"""
import asyncio
import os

import pytest

import app.agent as agent_mod
from app.agent import build_agent
from app.errors import SetupError
from tests.conftest import make_settings
from tests.fakes import ScriptedModel

# Read now: the autouse clean_env fixture clears these before each test.
LIVE = {k: os.environ.get(k, "").strip() for k in ("CDATA_USERNAME", "CDATA_PAT")}

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("RUN_LIVE_TESTS") != "1", reason="set RUN_LIVE_TESTS=1"),
    pytest.mark.skipif(not (LIVE["CDATA_USERNAME"] and LIVE["CDATA_PAT"]),
                       reason="needs CDATA_USERNAME and CDATA_PAT"),
]


@pytest.fixture
def no_llm(monkeypatch):
    monkeypatch.setattr(agent_mod, "init_chat_model", lambda *a, **k: ScriptedModel())


def test_mcp_tools_load_with_real_credentials(no_llm):
    settings = make_settings(cdata_username=LIVE["CDATA_USERNAME"], cdata_pat=LIVE["CDATA_PAT"])
    _, names, _ = asyncio.run(build_agent(settings, checkpointer=None))
    assert {"getCatalogs", "getTables", "getColumns", "queryData"} <= set(names)


def test_a_bad_pat_is_reported_as_rejected_credentials(no_llm):
    settings = make_settings(cdata_username=LIVE["CDATA_USERNAME"], cdata_pat="not-a-real-pat")
    with pytest.raises(SetupError, match=r"rejected the credentials \(HTTP 401\)"):
        asyncio.run(build_agent(settings, checkpointer=None))
