#!/usr/bin/env bash
# LoveLetter_Linux.sh — a safe, local "surprise" for Linux
set -euo pipefail

# ---- configuration ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/LoveLetter_Log.txt"
NOTE_FILE="$SCRIPT_DIR/.HiddenNote.txt"   # hidden by dot
MUSIC_FILE="$SCRIPT_DIR/background.wav"  # optional WAV placed beside script
TOTAL_SEC=300                             # 5 minutes
STEPS=100                                 # progress steps (percent)
STEP_SLEEP=$(awk "BEGIN { printf \"%.4f\", $TOTAL_SEC/$STEPS }")

# ---- helpers ----
log() { printf "[%s] %s\n" "$(date '+%F %T')" "$*" | tee -a "$LOG_FILE"; }

# start
log "Script started."

# intro dialog (zenity)
zenity --info --title="A Little Surprise" --no-wrap --text="I love you ❤️\n\nThis is a little, calm surprise. Sit back for 5 minutes." || true
log "Shown intro dialog."

# optional background audio (paplay or ffplay fallback)
AUDIO_PID=""
if [[ -f "$MUSIC_FILE" ]]; then
  if command -v paplay >/dev/null 2>&1; then
    log "Playing background audio (paplay): $MUSIC_FILE"
    paplay "$MUSIC_FILE" & AUDIO_PID=$!
  elif command -v ffplay >/dev/null 2>&1; then
    log "Playing background audio (ffplay): $MUSIC_FILE"
    ffplay -nodisp -autoexit -hide_banner -loglevel error "$MUSIC_FILE" >/dev/null 2>&1 & AUDIO_PID=$!
  else
    log "Audio file present but no player found (paplay/ffplay). Skipping audio."
  fi
else
  log "No background audio file found."
fi

# system info dialog (local, poetic)
SYSINFO="$(uname -srmo 2>/dev/null || true)
$(awk '/MemTotal|MemFree/ {print}' /proc/meminfo 2>/dev/null | sed -n '1,2p')
$(lscpu 2>/dev/null | sed -n '1,6p')"

echo "$SYSINFO" | zenity --text-info --title="Your Machine — a few poetic facts" --width=640 --height=260 || true
log "Displayed system info."

# create a named pipe for progress output to zenity
PIPE="/tmp/loveletter_progress_$$.pipe"
trap 'rm -f "$PIPE"; log "Cleaned up."; exit' EXIT
mkfifo "$PIPE"

# feed progress in background to zenity
(
  # initial header line for zenity progress (percent)
  for i in $(seq 0 $STEPS); do
    pct=$i
    remain=$(( (TOTAL_SEC * (STEPS - i)) / STEPS ))
    # send percentage and message lines to zenity
    echo "$pct"
    echo "# Time left: $(printf '%02d:%02d' $((remain/60)) $((remain%60)))"
    sleep "$STEP_SLEEP"
  done
) > "$PIPE" &

# run zenity progress (reads from pipe). --auto-close closes when 100 reached
zenity --progress --title="A Short, Quiet Journey" --auto-close --percentage=0 --width=540 < "$PIPE" || true
log "Progress dialog finished."

# create the hidden note
cat > "$NOTE_FILE" <<'EOF'
💌 My secret note
------------------------
Created on: <<CREATED_AT>>
Dear reader,
Curiosity can be gentle; the kindest code leaves no scars.
Be kind to your machine; it trusts you completely.
EOF

# replace placeholder with actual timestamp
sed -i "s|<<CREATED_AT>>|$(date '+%F %T')|" "$NOTE_FILE"
chmod 600 "$NOTE_FILE"
log "Hidden note created at $NOTE_FILE"

# stop background audio if started
if [[ -n "${AUDIO_PID:-}" ]]; then
  log "Stopping audio (pid $AUDIO_PID)."
  kill "$AUDIO_PID" 2>/dev/null || true
fi

# final dialog + desktop notification (if available)
zenity --info --title="End of Surprise" --no-wrap --text="The time has passed.\n\nA small note now rests quietly in this folder." || true
if command -v notify-send >/dev/null 2>&1; then
  notify-send "Surprise complete" "Hidden note created in the folder."
fi
log "Final dialog shown. Script finished."

# cleanup
rm -f "$PIPE"
log "Removed temporary pipe. Exiting."
exit 0
