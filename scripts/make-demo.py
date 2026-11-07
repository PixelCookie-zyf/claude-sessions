#!/usr/bin/env python3
"""Generate a fake ~/.claude/projects tree for screenshots and testing.

    python3 scripts/make-demo.py /tmp/cc-demo
    CC_SESSIONS_PROJECTS=/tmp/cc-demo CC_SESSIONS_CACHE=/tmp/cc-demo-cache ./cc-sessions

Everything here is fictional.
"""
import json, os, sys, time, uuid

HOME = os.path.expanduser("~")
NOW = time.time()
H, D = 3600, 86400

SESSIONS = [
    # project, branch, age, title kind, title, cost, tokens, turns
    ("web-dashboard", "feat/oauth", 20, "custom", "Refactor auth flow to OAuth PKCE", 4.12, 9_800_000, None),
    ("rust-indexer", "main", 2 * H, "ai", "Speed up file indexer with rayon", 2.37, 5_400_000, None),
    ("ml-notebooks", "main", 26 * H, "ai", "Fine-tune tokenizer on a code corpus", 7.80, 18_200_000, None),
    ("blog", "astro-5", 3 * D, "custom", "Migrate blog to Astro 5", 1.94, 3_100_000, None),
    ("infra", "main", 5 * D, "ai", "Terraform: split prod / staging state", 3.05, 6_700_000, None),
    ("game-jam", "main", 8 * D, "ai", "Low-poly island water shader", 5.61, 12_900_000, None),
    ("dotfiles", "main", 15 * D, "first", "my zsh prompt takes 400ms to start, can you profile it and make it faster?", 0.48, 820_000, None),
    ("api-server", "fix/n-plus-one", 22 * D, "custom", "Fix N+1 queries in /orders endpoint", 2.66, 4_900_000, None),
    ("mobile-app", "main", 64 * D, "ai", "React Native offline sync queue", 6.20, 14_300_000, None),
]

FEATURED = [  # conversation for the first session (the one selected in the screenshot)
    ("user", "The login flow still uses the implicit grant. Can you move it to OAuth 2.1 with PKCE? Keep the existing session cookie."),
    ("assistant", [("tool", "Grep", "implicit grant usage in src/auth"),
                   ("tool", "Read", "src/auth/login.ts"),
                   ("text", "Found it. The implicit grant lives in `src/auth/login.ts` and the callback in `src/auth/callback.ts`.\n\n## Plan\n- Generate a `code_verifier` and `S256` challenge per login attempt\n- Store the verifier in a short-lived, http-only cookie\n- Exchange the code on the server, then set the existing session cookie\n\nNothing changes for already signed-in users.")]),
    ("user", "Sounds good, go ahead. Please add tests for the verifier cookie expiring."),
    ("assistant", [("tool", "Edit", "src/auth/login.ts"),
                   ("tool", "Write", "src/auth/pkce.ts"),
                   ("tool", "Edit", "src/auth/callback.ts"),
                   ("tool", "Bash", "Run auth test suite"),
                   ("text", "Done. **18 tests pass**, including two new ones:\n\n- verifier cookie expires after 10 minutes\n- callback rejects a reused `state`\n\nThe implicit-grant code path is removed.")]),
    ("command", "/compact"),
    ("user", "Can you also update the README section about local login?"),
    ("assistant", [("tool", "Edit", "README.md"),
                   ("text", "Updated *Local development → Login* with the new redirect URI and the `AUTH_PKCE=1` flag.")]),
]


def line(f, obj):
    f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")  # compact, like Claude Code


def iso(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(ts))


def write_session(root, idx, proj, branch, age, kind, title, cost, tokens):
    cwd = os.path.join(HOME, "code", proj)
    pdir = os.path.join(root, cwd.replace("/", "-"))
    os.makedirs(pdir, exist_ok=True)
    sid = str(uuid.UUID(int=0x1C0DE000 + idx * 7919))
    path = os.path.join(pdir, sid + ".jsonl")
    end = NOW - age
    convo = FEATURED if idx == 0 else [
        ("user", title if kind == "first" else "Let's work on: " + title.lower()),
        ("assistant", [("tool", "Read", "README.md"), ("text", "Sure, starting with a quick look at the project layout.")]),
        ("user", "looks right, continue"),
        ("assistant", [("tool", "Bash", "Run tests"), ("text", "All green. Summary of the change is above.")]),
    ]
    t = end - 40 * 60
    step = (end - t) / (len(convo) + 1)
    n = 0
    with open(path, "w") as f:
        for role, body in convo:
            t += step
            if role == "user":
                line(f, {"type": "user", "cwd": cwd, "gitBranch": branch, "sessionId": sid, "timestamp": iso(t),
                         "message": {"role": "user", "content": body}})
            elif role == "command":
                line(f, {"type": "user", "cwd": cwd, "gitBranch": branch, "sessionId": sid, "timestamp": iso(t),
                         "message": {"role": "user", "content": "<command-name>%s</command-name>\n<command-args></command-args>" % body}})
            else:
                for b in body:
                    n += 1
                    if b[0] == "tool":
                        content = [{"type": "tool_use", "id": "toolu_%d" % n, "name": b[1],
                                    "input": {"description": b[2]}}]
                    else:
                        content = [{"type": "text", "text": b[1]}]
                    line(f, {"type": "assistant", "sessionId": sid, "timestamp": iso(t),
                             "message": {"id": "msg_demo%04d%03d" % (idx, n), "model": "claude-opus-5-5",
                                         "role": "assistant", "content": content}})
        if kind == "custom":
            line(f, {"type": "custom-title", "customTitle": title, "sessionId": sid})
        elif kind == "ai":
            line(f, {"type": "ai-title", "aiTitle": title, "sessionId": sid})
        line(f, {"type": "cost-state", "sessionId": sid, "totalCostUSD": cost,
                 "modelUsage": {"claude-opus-5-5": {"inputTokens": tokens // 200, "outputTokens": tokens // 60,
                                                    "cacheReadInputTokens": tokens - tokens // 200 - tokens // 60,
                                                    "cacheCreationInputTokens": 0}}})
    os.utime(path, (end, end))


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cc-demo")
    os.makedirs(root, exist_ok=True)
    for i, (proj, branch, age, kind, title, cost, tokens, _) in enumerate(SESSIONS):
        write_session(root, i, proj, branch, age, kind, title, cost, tokens)
    print(root)


if __name__ == "__main__":
    main()
