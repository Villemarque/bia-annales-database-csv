#!/bin/sh

newTmuxSessionScript() {
  local SESSION_NAME=$1
  tmux new-session -s "$SESSION_NAME" -d
  tmux split-window -d
  tmux split-window -d
  tmux split-window -d
  tmux send-keys -t "$SESSION_NAME".1 "pnpm run dev --open" C-m
  #tmux send-keys -t "$SESSION_NAME".2 "py3 -m http.server" C-m
  #tmux send-keys -t "$SESSION_NAME".4 "scala-cli --jvm system index.scala > index.html" C-m
  tmux attach-session -t "$SESSION_NAME"
}

newTmuxSessionScript bia-site