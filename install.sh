#!/bin/sh
# Install cc-sessions: link the script into ~/.local/bin and (optionally) install the ClaudeMark font.
#   ./install.sh            link script + install font
#   ./install.sh --no-font  link script only (the UI falls back to ✻)
set -e
here=$(cd "$(dirname "$0")" && pwd)
bin="${CC_SESSIONS_BIN:-$HOME/.local/bin}"

command -v python3 >/dev/null || { echo "cc-sessions needs python3"; exit 1; }
command -v fzf >/dev/null || echo "note: fzf not found - install it (brew install fzf) for the interactive UI"

mkdir -p "$bin"
chmod +x "$here/cc-sessions"
ln -sf "$here/cc-sessions" "$bin/cc-sessions"
echo "linked  $bin/cc-sessions -> $here/cc-sessions"

if [ "$1" != "--no-font" ]; then
  case "$(uname)" in
    Darwin) fonts="$HOME/Library/Fonts" ;;
    *)      fonts="$HOME/.local/share/fonts" ;;
  esac
  mkdir -p "$fonts"
  cp "$here/fonts/ClaudeMark.ttf" "$fonts/"
  command -v fc-cache >/dev/null && fc-cache -f "$fonts" >/dev/null 2>&1 || true
  echo "font    $fonts/ClaudeMark.ttf  (restart your terminal if the logo shows as a box)"
fi

case ":$PATH:" in
  *":$bin:"*) ;;
  *) echo "note: add $bin to your PATH" ;;
esac
echo "done    run: cc-sessions"
