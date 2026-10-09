#!/usr/bin/env bash
# Overnight autonomous loop: fresh OpenCode session per iteration.
# Each session must commit+push its progress before finishing; the next
# session is prompted from the updated repo (NOTES.md = source of truth).
set -uo pipefail

REPO=/home/Dcs102/lightburn
LOGDIR=$REPO/loop-logs
ITERATIONS=${ITERATIONS:-8}
TIMEOUT=${TIMEOUT:-6h}
MODEL="unsloth/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF"

mkdir -p "$LOGDIR"
cd "$REPO" || exit 1

PROMPT=$(cat <<'EOF'
You are one iteration of an autonomous overnight loop working on the LightBurn v1.1.03 reverse-engineering project in this directory. A fresh session starts after you finish, with no memory of this one — the repository is the only handoff.

RULES (strict):
1. FIRST read AGENTS.md and NOTES.md. NOTES.md is the source of truth; do NOT re-derive what they state. Check `git log --oneline -5` to see what previous iterations did.
2. Advance ONE concrete step toward the goal in HANDOFF.md ("WHAT TO DO NEXT"). Prefer small, verifiable increments that can be finished in this session. Do not start a large sub-project you cannot complete here.
3. Keep NOTES.md current: record verified findings with exact addresses/paths; flag anything uncertain. Update AGENTS.md only for new environment gotchas.
4. The Ghidra MCP headless server is at http://127.0.0.1:8089 (systemd user svc ghidra-mcp-headless). If it is down, run `systemctl --user restart ghidra-mcp-headless` and wait for it to come up before relying on it.
5. BEFORE you finish you MUST commit and push: stage your changes, write a specific commit message describing what you found/changed, then `git push`. If there is nothing new to say, still verify the repo state is clean and pushed. A session that does not push has wasted its work.
6. Do NOT modify git remote URLs, .gitignore, or loop-logs/. Do NOT create a GitHub repo or release. Work stays in this directory.
7. Finish with a short summary (<=15 lines) of: what you verified, exact addresses/artifacts found, and the recommended next step for the next session.
EOF
)

for i in $(seq 1 "$ITERATIONS"); do
  ts=$(date +%Y%m%d-%H%M%S)
  log="$LOGDIR/iter-$i-$ts.log"
  echo "=== iter $i/$ITERATIONS start $(date -Is) ===" | tee -a "$log"

  # Sync to latest pushed state (also guards against partial local commits)
  git pull --ff-only >>"$log" 2>&1 || echo "WARN: git pull failed, continuing with local state" | tee -a "$log"

  timeout "$TIMEOUT" opencode run \
    --dir "$REPO" \
    --model "$MODEL" \
    --auto \
    --title "lightburn-loop-iter-$i" \
    "$PROMPT" >>"$log" 2>&1
  rc=$?

  echo "=== iter $i opencode exit=$rc $(date -Is) ===" | tee -a "$log"
  git log --oneline -3 >>"$log" 2>&1

  # Safety net: if the session left uncommitted work, commit+push it ourselves
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "SAFETY-NET: committing uncommitted work from iter $i" | tee -a "$log"
    git add -A >>"$log" 2>&1
    git commit -m "loop-iter-$i: auto-commit of unpushed session work (safety net)" >>"$log" 2>&1 || true
  fi
  git push >>"$log" 2>&1 && echo "PUSHED after iter $i" | tee -a "$log" || echo "ERROR: push failed after iter $i" | tee -a "$log"
done

echo "=== loop complete $(date -Is) ==="
git log --oneline -10
