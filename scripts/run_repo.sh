#!/bin/bash
# usage: run_repo.sh OWNER/REPO OUTDIR   (env: SCANNER_REF, TARGET_KGP)
# Clones the project, runs kotlin24-ready, then `gradle help` with the original Kotlin Gradle plugin version ("before")
# and with TARGET_KGP substituted ("after"). `help` only evaluates the build scripts: it does not compile Kotlin sources.
set -u
repo=$1; out=$2; target=${TARGET_KGP:-2.4.20}
mkdir -p "$out"; rm -rf work
git clone -q --depth 1 "https://github.com/$repo.git" work || { echo '{"repo":"'$repo'","error":"clone failed"}' > "$out/result.json"; exit 0; }
cd work
sha=$(git rev-parse HEAD)
kotlin24-ready . -f json --fail-on never > "$out/findings.json" 2> "$out/scan.err"
wrapper=$(grep -m1 distributionUrl gradle/wrapper/gradle-wrapper.properties 2>/dev/null | sed 's/.*gradle-\(.*\)-\(bin\|all\).zip/\1/')
chmod +x gradlew 2>/dev/null
G=(./gradlew help --console=plain --no-daemon --warning-mode none -Dorg.gradle.jvmargs=-Xmx3g)
run() { # name
  timeout 1200 "${G[@]}" > "$out/$1.log" 2>&1; echo $? > "$out/$1.rc"
}
run before
python3 ../scripts/sub.py . "$target" > "$out/sub.txt"
subs=$(grep '^total:' "$out/sub.txt" | cut -d' ' -f2)
if [ "${subs:-0}" -gt 0 ]; then run after; else echo skipped > "$out/after.rc"; fi
python3 - "$repo" "$sha" "$wrapper" "$subs" "$out" <<'PY'
import json, os, re, sys
repo, sha, wrapper, subs, out = sys.argv[1:6]
def rc(n):
    try: return open(f"{out}/{n}.rc").read().strip()
    except OSError: return None
def tail(n):
    try: t = open(f"{out}/{n}.log", errors="replace").read()
    except OSError: return ""
    m = re.search(r"\* What went wrong:\n(.*?)\n\n", t, re.S)
    errs = [l for l in t.splitlines() if l.startswith("e: ") or "Unresolved reference" in l][:12]
    return {"what_went_wrong": (m.group(1)[:1200] if m else ""), "e_lines": errs}
f = {}
try: f = json.load(open(f"{out}/findings.json"))
except Exception: pass
res = {"repo": repo, "sha": sha, "wrapper_gradle": wrapper, "substitutions": int(subs or 0), "rc_before": rc("before"), "rc_after": rc("after"),
       "kgp_detected": f.get("kgpDetected"), "findings": [{k: x[k] for k in ("rule", "severity", "file", "line")} for x in f.get("findings", [])],
       "after_error": tail("after") if rc("after") not in (None, "0", "skipped") else None,
       "before_error": tail("before") if rc("before") not in (None, "0") else None}
json.dump(res, open(f"{out}/result.json", "w"), indent=1)
print(json.dumps({k: res[k] for k in ("repo", "rc_before", "rc_after", "substitutions")}))
PY
