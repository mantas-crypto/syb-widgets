"""
Runs scripts/refresh.py inside GitHub Actions (see .github/workflows/refresh.yml).

refresh.py was written for the Composio workbench, which hands it two helpers:
    proxy_execute(...)       GitHub API calls through Composio's GitHub connection
    run_composio_tool(...)   Composio tools, here only INSTAGRAM_GET_IG_USER_MEDIA
This file supplies the same two helpers so refresh.py itself stays unchanged:
    GitHub     the job's own GITHUB_TOKEN (needs "contents: write"), straight to api.github.com
    Instagram  Composio's REST API with the repo secret COMPOSIO_API_KEY

Environment
    GITHUB_TOKEN          set by the workflow
    COMPOSIO_API_KEY      repo secret (Composio dashboard, API keys)
    COMPOSIO_IG_ACCOUNT   optional: the Composio connected account id for Instagram.
                          Left empty, the one ACTIVE Instagram connection is used.
    REFRESH_DRY           "true" = read everything, commit nothing (the test button)
    REFRESH_FULL          "true" = re-read every Instagram post
"""
import json
import os
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSIO = os.environ.get("COMPOSIO_BASE_URL", "https://backend.composio.dev/api/v3.1")
_ig_account = None


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


def _composio(method, path, **kw):
    r = _request(method, COMPOSIO + path, headers={"x-api-key": _need("COMPOSIO_API_KEY")}, **kw)
    if r.status_code in (401, 403):
        raise RuntimeError("Composio rejected the API key (HTTP %s). Check the COMPOSIO_API_KEY secret." % r.status_code)
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


def run_composio_tool(tool_slug, arguments, account=None):
    """Same call shape as the workbench helper. Returns (result, error); result["data"] is the tool output."""
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
