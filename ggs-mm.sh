#!/usr/bin/env bash
readonly APP_NAME='ggs-mm'

readonly DATA_HOME="${XDG_DATA_HOME:-"${HOME?'HOME is not set'}/.local/share"}/$APP_NAME"
readonly CONFIG_HOME="${XDG_CONFIG_HOME:-"${HOME?'HOME is not set'}/.config"}/$APP_NAME"
# STATE is for data that should "persist between (application) restarts, but that is not important or portable enough
# to the user that it should be stored in [DATA]"
# examples include
#   * logs and history
#   * application state which may be used on restart
# source: 
#   freedesktop
#   XDG Base Directory Specification
#   https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
readonly STATE_HOME="${XDG_STATE_HOME:-"${HOME?'HOME is not set'}/.local/state"}/$APP_NAME"

readonly LOG_FILE="$STATE_HOME/log"

readonly INSTALL_DIR_NAME='~mods'
INSTALL_PARENT_DIR=""
MODS_DIR="$DATA_HOME/mods"

# Create directories and files
#   * DATA_HOME, CONFIG_HOME, STATE_HOME
#   * log
function init_dirs() {
  mkdir -p "$DATA_HOME" "$CONFIG_HOME" "$STATE_HOME"
  touch "$LOG_FILE"
}

function clear_log() {
  echo 'Cleared log' > "$LOG_FILE"
}

function clean_self() {
  rm -r "$DATA_HOME" "$CONFIG_HOME" "$STATE_HOME"
}

function verify_dir() {
  local input="$1"
  if (( "$#" > 1 )); then
    echo "[ERROR] Only 1 input is allowed"
    exit 1
  fi
  if [ ! -d "$input" ]; then
    echo "[ERROR] '$input' is not a directory"
    exit 1
  fi
  return 0
} 2>&1

function setup_config() {
  local -r config_file="$CONFIG_HOME/config"
  let line_no=0
  while read -r line; do
    line_no=$((line_no + 1))
    lhs="${line%%'='*}"
    rhs="${line##*'='}"
    rhs="${rhs/'~'/$HOME}"

    case "$lhs" in
      "install_parent_dir")
        verify_dir "$rhs"
        INSTALL_PARENT_DIR="$rhs"
        echo "set INSTALL_PARENT_DIR='$rhs'"
        ;;
      "mods_dir")
        verify_dir "$rhs"
        MODS_DIR="$rhs"
        echo "set MODS_DIR='$rhs'"
        ;;
      ""|" ") ;;
      *)
        echo "[ERROR] Unrecognized parameter ($line_no): '$lhs'"
        exit 5
        ;;
    esac
  done < "$config_file"
}

function install_mods() {
  local -r mods_dir=$1
  local -r install_parent_dir=$2
  local -r install_dir="$install_parent_dir/$INSTALL_DIR_NAME"

  verify_dir "$mods_dir"
  verify_dir "$install_parent_dir"
  
  mkdir --verbose --parents "$install_dir"
  cp --verbose --interactive --recursive "$mods_dir" "$install_dir"
}

function uninstall_mods() {
  local -r install_parent_dir=$1
  local -r install_dir="$install_parent_dir/$INSTALL_DIR_NAME"

  verify_dir "$install_parent_dir"

  rm --verbose --recursive "$install_dir"
}

function main() {
  init_dirs
  setup_config

  case "$1" in
    "install")
      install_mods "$MODS_DIR" "$INSTALL_PARENT_DIR"
      ;;
    "uninstall")
      uninstall_mods "$INSTALL_PARENT_DIR"
      ;;
    "clear-log")
      clear_log
      ;;
    "")
      echo "[ERROR] No subcommand given" 2>&1
      exit 3
      ;;
    *)
      echo "[ERROR] Unrecognized subcommand" 2>&1
      exit 2
  esac
}

# du -- Gets size of a file or directory
# wc -- Counts words(, lines, or bytes, and probably more) of a file or stdin
main "$@" | tee -a -p "$LOG_FILE"

