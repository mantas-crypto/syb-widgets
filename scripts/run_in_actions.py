"""
Runs scripts/refresh.py inside GitHub Actions (see .github/workflows/refresh.yml).

refresh.py was written for the Composio workbench, which hands it two helpers:
    proxy_execute(...)       GitHub API calls through Composio's GitHub connection
    run_composio_tool(...)   Composio tools, here only INSTAGRAM_GET_IG_USER_MEDIA
This file supplies the same two helpers so refresh.py itself stays unchanged:
    GitHub     the job's own GITHUB_TOKEN (needs "contents: write"), straight to api.github.com
    Instagram  Composio, with the repo secret COMPOSIO_API_KEY. A key that starts with ck_ (the personal
               key from Composio's app) goes through Composio Connect; ak_ / uak_ keys use the REST API.

Environment
    GITHUB_TOKEN          set by the workflow
    COMPOSIO_API_KEY      repo secret (Composio dashboard, API keys)
    COMPOSIO_IG_ACCOUNT   optional: which Composio Instagram connection to use. Left empty, the job
                          finds the one that answers as @surfyogabeer.
    REFRESH_DRY           "true" = read everything, commit nothing (the test button)
    REFRESH_FULL          "true" = re-read every Instagram post
"""
import json
import os
import re
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSIO = os.environ.get("COMPOSIO_BASE_URL", "https://backend.composio.dev/api/v3.1")
_ig_account = None
MAX_DAILY_DELETES = 40


def _flag(name):
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def _need(name):
    v = os.environ.get(name, "").strip()
    if not v:
        raise SystemExit("Missing %s. Add it under repo Settings, Secrets and variables, Actions." % name)
    return v


def _request(method, url, tries=3, **kw):
    """One HTTP call, retried on network errors and 5xx / rate limits."""
    for i in range(tries):
        try:
            r = requests.request(method, url, timeout=60, **kw)
            if r.status_code < 500 and r.status_code != 429:
                return r
            err = "HTTP %s %s" % (r.status_code, r.text[:200])
        except requests.RequestException as e:
            err = str(e)
        if i < tries - 1:
            time.sleep(2 * (i + 1))
    raise RuntimeError("%s %s: %s" % (method, url.split("?")[0], err))


def proxy_execute(method, endpoint, toolkit, query_params=None, body=None):
    """Same call shape as the workbench helper. Returns (json, error)."""
    if toolkit != "github":
        return None, "only the github toolkit is wired up here"
    try:
        r = _request(method, "https://api.github.com" + endpoint, params=query_params, json=body,
                     headers={"Authorization": "Bearer " + _need("GITHUB_TOKEN"),
                              "Accept": "application/vnd.github+json",
                              "X-GitHub-Api-Version": "2022-11-28"})
    except RuntimeError as e:
        return None, str(e)
    if r.status_code >= 400:
        return None, "HTTP %s %s" % (r.status_code, r.text[:300])
    return r.json(), None


_key_header = None   # which header this key works with, once known


def _key_shape(k):
    """Describes the key without showing it, for the log."""
    kind = next((p for p in ("uak_", "ak_", "ck_") if k.startswith(p)), "something else")
    odd = ", has spaces or line breaks inside" if len(k.split()) > 1 else ""
    return "length %d, starts with %s%s" % (len(k), kind, odd)


def _composio(method, path, **kw):
    global _key_header
    key = _need("COMPOSIO_API_KEY")
    # project keys go in x-api-key, personal (user) keys in x-user-api-key: use whichever is accepted
    for h in ([_key_header] if _key_header else ["x-api-key", "x-user-api-key"]):
        r = _request(method, COMPOSIO + path, headers={h: key}, **kw)
        if r.status_code not in (401, 403):
            _key_header = h
            break
    if r.status_code in (401, 403):
        raise RuntimeError("Composio rejected the API key (HTTP %s). The saved key: %s. Composio said: %s"
                           % (r.status_code, _key_shape(key), r.text[:200].replace(key, "<key>")))
    if r.status_code >= 400:
        raise RuntimeError("Composio HTTP %s %s" % (r.status_code, r.text[:300]))
    return r.json()


def _instagram_account():
    global _ig_account
    if _ig_account:
        return _ig_account
    _ig_account = os.environ.get("COMPOSIO_IG_ACCOUNT", "").strip()
    if not _ig_account:
        items = _composio("GET", "/connected_accounts",
                          params={"toolkit_slugs": "instagram", "statuses": "ACTIVE"}).get("items") or []
        items = [a for a in items if ((a.get("toolkit") or {}).get("slug") or "").lower() == "instagram"
                 and (a.get("status") or "ACTIVE").upper() == "ACTIVE"]
        if not items:
            raise RuntimeError("this Composio API key sees no active Instagram connection. Reconnect Instagram in "
                               "Composio, or make the key in the same Composio project that holds the connection.")
        if len(items) > 1:
            raise RuntimeError("this Composio API key sees %d active Instagram connections. Put the id of the "
                               "@surfyogabeer one in the repo variable COMPOSIO_IG_ACCOUNT." % len(items))
        _ig_account = items[0]["id"]
    return _ig_account


# ---------- Composio Connect (keys that start with ck_) ----------
# A ck_ key is the personal key from Composio's own app (Settings, Sessions & API Key). It reaches the
# same connected accounts Claude uses, but only through Composio's MCP endpoint, not the REST API above.
CONNECT_MCP = os.environ.get("COMPOSIO_MCP_URL", "https://connect.composio.dev/mcp")
IG_USERNAME = os.environ.get("IG_USERNAME", "surfyogabeer")
_mcp = {"session": None, "id": 0}


def _mcp_post(payload):
    key = _need("COMPOSIO_API_KEY")
    h = {"x-consumer-api-key": key, "Content-Type": "application/json",
         "Accept": "application/json, text/event-stream"}
    if _mcp["session"]:
        h["Mcp-Session-Id"] = _mcp["session"]
    r = _request("POST", CONNECT_MCP, headers=h, json=payload)
    if r.status_code in (401, 403):
        raise RuntimeError("Composio rejected the API key (HTTP %s). The saved key: %s. Composio said: %s"
                           % (r.status_code, _key_shape(key), r.text[:200].replace(key, "<key>")))
    if r.status_code >= 400:
        raise RuntimeError("Composio HTTP %s %s" % (r.status_code, r.text[:300]))
    if r.headers.get("Mcp-Session-Id"):
        _mcp["session"] = r.headers["Mcp-Session-Id"]
    if "id" not in payload:          # a notification: no answer expected
        return None
    text = r.content.decode("utf-8", "replace")   # may be plain JSON or an event stream
    msgs = []
    if "text/event-stream" in r.headers.get("Content-Type", ""):
        for block in text.replace("\r\n", "\n").split("\n\n"):
            data = "\n".join(l[5:].lstrip() for l in block.split("\n") if l.startswith("data:"))
            if data:
                try:
                    msgs.append(json.loads(data))
                except ValueError:
                    pass
    else:
        msgs = [json.loads(text)]
    for m in msgs:
        if isinstance(m, dict) and m.get("id") == payload["id"]:
            if m.get("error"):
                raise RuntimeError("Composio: %s" % str(m["error"])[:300])
            return m.get("result") or {}
    raise RuntimeError("Composio sent no answer to %s" % payload.get("method"))


def _mcp_call(method, params):
    if _mcp["session"] is None and method != "initialize":
        _mcp_call("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                 "clientInfo": {"name": "syb-widgets-refresh", "version": "1"}})
        _mcp["session"] = _mcp["session"] or ""     # some servers keep no session: do not start over
        _mcp_post({"jsonrpc": "2.0", "method": "notifications/initialized"})
    _mcp["id"] += 1
    return _mcp_post({"jsonrpc": "2.0", "id": _mcp["id"], "method": method, "params": params})


def _connect_tool(tool_slug, arguments, account=None):
    """One tool through Composio Connect. Returns (tool response dict, error text)."""
    item = {"tool_slug": tool_slug, "arguments": arguments}
    if account:
        item["account"] = account
    res = _mcp_call("tools/call", {"name": "COMPOSIO_MULTI_EXECUTE_TOOL",
                                   "arguments": {"tools": [item], "sync_response_to_workbench": False}})
    text = "".join(c.get("text", "") for c in (res.get("content") or []) if c.get("type") == "text")
    try:
        j = json.loads(text)
    except ValueError:
        return None, (text or "empty answer from Composio")[:300]
    rows = ((j.get("data") or {}).get("results")) or []
    row = rows[0] if rows else {}
    if row.get("error") or not row.get("response"):
        return None, str(row.get("error") or j.get("error") or "tool call was not successful")[:400]
    resp = row["response"]
    if not resp.get("successful", True) or resp.get("error"):
        return None, str(resp.get("error") or "tool call was not successful")[:400]
    return resp, None


def _connect_instagram_account(first_error):
    """Composio holds more than one Instagram connection: pick the one that is really our account."""
    global _ig_account
    names = re.findall(r'"([A-Za-z0-9_.\-]+)"', first_error.split("account' field", 1)[-1])
    for name in names:
        r, e = _connect_tool("INSTAGRAM_GET_IG_USER_MEDIA",
                             {"ig_user_id": "me", "limit": 1, "fields": "id,username"}, name)
        rows = ((r or {}).get("data") or {}).get("data") or []
        if rows and (rows[0].get("username") or "").lower() == IG_USERNAME.lower():
            _ig_account = name
            return name
    raise RuntimeError("Composio holds several Instagram connections and none of them answered as @%s (%s). "
                       "Put the right one in the repo variable COMPOSIO_IG_ACCOUNT." % (IG_USERNAME, ", ".join(names)))


def _run_via_connect(tool_slug, arguments, account=None):
    global _ig_account
    try:
        _ig_account = _ig_account or os.environ.get("COMPOSIO_IG_ACCOUNT", "").strip() or None
        r, e = _connect_tool(tool_slug, arguments, account or _ig_account)
        if e and "Specify which to use" in e and not (account or _ig_account):
            r, e = _connect_tool(tool_slug, arguments, _connect_instagram_account(e))
        return r, e
    except RuntimeError as ex:
        return None, str(ex)


def run_composio_tool(tool_slug, arguments, account=None):
    """Same call shape as the workbench helper. Returns (result, error); result["data"] is the tool output."""
    if _need("COMPOSIO_API_KEY").startswith("ck_"):
        return _run_via_connect(tool_slug, arguments, account)
    try:
        j = _composio("POST", "/tools/execute/" + tool_slug,
                      json={"arguments": arguments, "connected_account_id": account or _instagram_account()})
    except RuntimeError as e:
        return None, str(e)
    if not j.get("successful", True) or j.get("error"):
        return None, str(j.get("error") or "tool call was not successful")[:300]
    d = j.get("data")
    if isinstance(d, dict) and "data" not in d and isinstance(d.get("response_data"), dict):
        j["data"] = d["response_data"]
    return j, None


def main():
    _need("GITHUB_TOKEN")
    _need("COMPOSIO_API_KEY")
    path = os.path.join(HERE, "refresh.py")
    ns = {"__name__": "syb_refresh", "proxy_execute": proxy_execute, "run_composio_tool": run_composio_tool}
    with open(path) as f:
        exec(compile(f.read(), path, "exec"), ns)

    # the workbench caps a cell at 180 seconds, so refresh.py budgets 140; no such cap here
    kw = {"budget": 900, "dry": _flag("REFRESH_DRY"), "full": _flag("REFRESH_FULL")}
    if not kw["dry"] and not kw["full"]:
        # Safety: a cut-short Instagram answer can look like "most posts were deleted" and would remove
        # their pictures from the repo. Rehearse first and stop if a daily run wants to delete a lot.
        rehearsal = ns["refresh"](**dict(kw, dry=True))
        if rehearsal.get("files_deleted", 0) > MAX_DAILY_DELETES:
            print(json.dumps(rehearsal, indent=1))
            raise SystemExit("Stopped before committing: this run wanted to delete %d files (limit %d). Instagram "
                             "probably returned a short list. Nothing was changed. If the deletions are real, run "
                             "the workflow by hand with \"full\" ticked."
                             % (rehearsal["files_deleted"], MAX_DAILY_DELETES))
    out = ns["refresh"](**kw)
    if out.get("partial"):
        out = {"first_run": out, **ns["refresh"](**kw)}

    text = json.dumps(out, indent=1)
    print(text)
    if not out.get("instagram_posts_read"):
        # the account has years of posts, so zero means the Instagram read did not really work
        raise SystemExit("Instagram returned no posts. Check the Instagram connection in Composio.")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write("### Widgets data refresh%s\n\n```json\n%s\n```\n" % (" (dry run)" if kw["dry"] else "", text))
    if out.get("reviews_error"):
        print("::warning title=Reviews not refreshed::%s" % out["reviews_error"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
