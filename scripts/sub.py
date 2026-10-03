#!/usr/bin/env python3
"""Replace the Kotlin Gradle plugin version of a checked-out project by TARGET. Prints one line per change. Standard library only."""
import os, re, sys

TARGET = sys.argv[2] if len(sys.argv) > 2 else "2.4.20"
root = sys.argv[1]
changes = 0


def edit(path, fn):
    global changes
    try:
        t = open(path, encoding="utf-8", errors="replace", newline="").read()
    except OSError:
        return
    n, k = fn(t)
    if k:
        open(path, "w", encoding="utf-8", newline="").write(n)
        changes += k
        print(f"{os.path.relpath(path, root)}: {k} change(s)")


def catalog(t):
    k = 0
    refs = set()
    for m in re.finditer(r'^\s*[\w.-]+\s*=\s*\{[^}\n]*id\s*=\s*"org\.jetbrains\.kotlin\.[^"]*"[^}\n]*version\.ref\s*=\s*"([^"]+)"', t, re.M):
        refs.add(m.group(1))
    for m in re.finditer(r'^\s*[\w.-]+\s*=\s*\{[^}\n]*version\.ref\s*=\s*"([^"]+)"[^}\n]*id\s*=\s*"org\.jetbrains\.kotlin\.[^"]*"', t, re.M):
        refs.add(m.group(1))
    names = refs | {"kotlin", "kotlin-version", "kotlinVersion", "kotlin_version"}

    def rep(m):
        nonlocal k
        if m.group(2) in names and m.group(3) != TARGET and re.match(r"\d", m.group(3)):
            k += 1
            return f'{m.group(1)}"{TARGET}"'
        return m.group(0)
    t = re.sub(r'^(\s*([\w.-]+)\s*=\s*)"([^"]+)"', rep, t, flags=re.M)
    # direct versions on kotlin plugins: id = "org.jetbrains.kotlin.x", version = "A"
    def rep2(m):
        nonlocal k
        if m.group(2) != TARGET and re.match(r"\d", m.group(2)):
            k += 1
            return m.group(1) + TARGET + m.group(3)
        return m.group(0)
    t = re.sub(r'(id\s*=\s*"org\.jetbrains\.kotlin\.[^"]*"\s*,\s*version\s*=\s*")([^"]+)(")', rep2, t)
    return t, k


def script(t):
    k = 0
    pats = [r'(kotlin\(\s*"[\w\-]+"\s*\)\s*version\s*")(\d[^"]*)(")',
            r'(id\s*\(?\s*["\']org\.jetbrains\.kotlin\.[\w.\-]+["\']\s*\)?\s*version\s*["\'])(\d[^"\']*)(["\'])',
            r'(org\.jetbrains\.kotlin:kotlin-gradle-plugin:)(\d[\w.\-]*)(["\'])']
    for p in pats:
        def rep(m):
            nonlocal k
            if m.group(2) == TARGET:
                return m.group(0)
            k += 1
            return m.group(1) + TARGET + m.group(3)
        t = re.sub(p, rep, t)
    return t, k


def props(t):
    k = 0

    def rep(m):
        nonlocal k
        if m.group(2) != TARGET:
            k += 1
            return m.group(1) + TARGET
        return m.group(0)
    return re.sub(r"^(kotlin(?:\.?[vV]ersion)\s*=\s*)(\d[\w.\-]*)", rep, t, flags=re.M), k


for dp, dns, fns in os.walk(root):
    dns[:] = [d for d in dns if d not in {".git", "build", ".gradle", "node_modules"}]
    for fn in fns:
        p = os.path.join(dp, fn)
        if fn.endswith(".versions.toml"):
            edit(p, catalog)
        elif fn.endswith((".gradle.kts", ".gradle")) or p.endswith(("buildSrc/build.gradle.kts", "build-logic/build.gradle.kts")):
            edit(p, script)
        elif fn == "gradle.properties":
            edit(p, props)
print(f"total: {changes}")
