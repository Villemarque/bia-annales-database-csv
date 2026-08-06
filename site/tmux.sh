#!/bin/sh

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

launchVersions() {
  local TARGET=$1
  local DEV_PANE
  local CHECK_PANE
  DEV_PANE=$(tmux split-window -d -P -F '#{pane_id}' -c "$SCRIPT_DIR" -t "$TARGET")
  CHECK_PANE=$(tmux split-window -d -P -F '#{pane_id}' -c "$SCRIPT_DIR" -t "$TARGET")
  tmux split-window -d -c "$SCRIPT_DIR" -t "$TARGET"
  tmux send-keys -t "$DEV_PANE" "pnpm run dev" C-m
  tmux send-keys -t "$CHECK_PANE" "pnpm run check:watch" C-m
  #tmux send-keys -t "$EXTRA_PANE" "scala-cli --jvm system index.scala > index.html" C-m
}

if [ -n "$TMUX" ]; then
  launchVersions "$(tmux display-message -p '#S')"
else
  tmux new-session -s bia-site -d -c "$SCRIPT_DIR"
  launchVersions bia-site
  tmux attach-session -t bia-site
fi