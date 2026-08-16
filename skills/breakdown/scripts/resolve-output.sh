#!/usr/bin/env sh
# Resolve /breakdown's two output paths to absolute, and refuse the ones that are not safe
# to write to.
#
# F4: `skills/breakdown-generate-tasks/output/2-backend/LAYER_SUMMARY.md` exists on disk,
# holding generated tasks for an unrelated project. Nothing was hardcoded -- the sub-skill was
# handed a *relative* directory and resolved it against its own, so a run's entire output
# landed inside the toolchain. The caller got no indication.
#
# The cause is that a relative path means nothing without saying what it is relative to, and a
# forked sub-skill does not share the caller's working directory. So resolution happens once,
# here, before anything is passed down.
#
# WHY A SCRIPT. §3.1 of the assessment says it outright: "The same doubt applies to every
# other prose guard in the toolchain, including 4.6's proposed absolute-path check. Writing
# more emphatic prose is not a fix." F15 is the evidence -- a correct, present, ignored guard.
#
# Usage:
#   resolve-output.sh <tasks-dir> [target-dir]
#
#   <tasks-dir>   where task XML is written; usually `docs/tasks/<slug>`. MAY be relative --
#                 it is resolved here, against this process's working directory, which is the
#                 caller's. That is the whole point.
#   [target-dir]  the value of --output-dir or --project-path: where code will be written.
#                 MUST be absolute; see below.
#
# On success, prints to stdout and exits 0:
#   tasks_dir=<absolute>
#   target_dir=<absolute>      (only when a target was given)
#
# On failure, prints `REFUSED: <reason>` to stderr and exits 1. It creates nothing, ever --
# in particular it does not create the directory it just refused.
#
# WHY THE TARGET MUST BE ABSOLUTE AND THE TASKS DIR NEED NOT
#
# They differ in whether a wrong answer is recoverable. `docs/tasks/<slug>` is the documented
# default, is always relative, and resolving it wrongly produces files in a visible place that
# can be deleted. `--output-dir` names where an entire codebase gets built and where /execute
# will later create branches and merge them; resolving *that* wrongly does real damage, and
# `./relative-out` gives no clue which directory the author had in mind. Refusing costs the
# caller one absolute path and removes the ambiguity entirely.

set -eu

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    echo "usage: $0 <tasks-dir> [target-dir]" >&2
    exit 2
fi

tasks_in=$1
target_in=${2:-}

refuse() {
    echo "REFUSED: $1" >&2
    exit 1
}

is_absolute() {
    # A leading `/`, or a drive letter -- Git Bash hands through `C:/x` and `C:\x` unchanged.
    case "$1" in
        /*|[A-Za-z]:*) return 0 ;;
        *) return 1 ;;
    esac
}

slashes() {
    # Backslashes to forward slashes, before anything else looks at the path.
    #
    # Not cosmetic. `dirname`/`basename` treat `\` as an ordinary character, and under MSYS
    # what survives gets mangled: `C:\Users\Lee\AppData\Local\Temp\nope\app` resolved to
    # `/tmp/nope/app` -- a directory nobody named, produced silently, with exit 0. That is the
    # F4 failure by a second route, inside the guard written to prevent it.
    printf '%s' "$1" | tr '\\' '/'
}

parent_of() {
    # `dirname` without calling dirname, for the reason above. Roots (`/`, `C:/`) are returned
    # with their trailing slash so the caller can detect that it has stopped moving.
    case "$1" in
        */*) ;;
        *) printf '%s' "$1"; return ;;      # no separator left: already at the top
    esac
    _up=${1%/*}
    case "$_up" in
        ''|[A-Za-z]:) _up="$_up/" ;;
    esac
    printf '%s' "$_up"
}

native_pwd() {
    # The path in the form the *host* understands, not the shell's private one. Git Bash's
    # `pwd -P` prints `/c/tmp/x`, which every downstream consumer on Windows -- python, the
    # Write tool, the sub-skills -- would fail to open. `pwd -W` prints `C:/tmp/x`. Elsewhere
    # `-W` is not a flag, and `pwd -P` is already the native form.
    ( cd "$1" 2>/dev/null || exit 1
      pwd -W 2>/dev/null || pwd -P )
}

abspath() {
    # Resolve to an absolute path. The directory need not exist yet, which matters: this runs
    # *before* /breakdown creates anything. Walk up to the deepest ancestor that does exist,
    # resolve that, and re-append the rest.
    _p=$(slashes "$1")
    is_absolute "$_p" || _p="$(native_pwd .)/$_p"
    _rest=''
    while [ ! -d "$_p" ]; do
        _parent=$(parent_of "$_p")
        [ "$_parent" = "$_p" ] && break
        _rest="${_p##*/}${_rest:+/$_rest}"
        _p=${_parent%/}
        [ -n "$_p" ] || _p=/
    done
    _p=$(native_pwd "$_p") || return 1
    printf '%s\n' "${_p%/}${_rest:+/$_rest}"
}

plugin_root() {
    # The nearest ancestor that is a Claude Code plugin, or nothing.
    _d=$1
    while :; do
        if [ -f "$_d/.claude-plugin/plugin.json" ]; then
            printf '%s\n' "$_d"
            return 0
        fi
        _parent=$(parent_of "$_d")
        [ "$_parent" = "$_d" ] && return 1
        _d=${_parent%/}
        [ -n "$_d" ] || return 1
    done
}

# ------------------------------------------------------------------- the target, if given
# Checked first: it is the argument the caller typed, so its error is the one worth reporting.
if [ -n "$target_in" ]; then
    is_absolute "$target_in" || refuse "$(printf '%s' \
        "--output-dir/--project-path must be an absolute path, not \`$target_in\`. Relative to what? This skill forks, so its working directory is not yours. Did you mean $(abspath "$target_in")?")"
    target_abs=$(abspath "$target_in") || refuse "cannot resolve target path: $target_in"
fi

tasks_abs=$(abspath "$tasks_in") || refuse "cannot resolve tasks path: $tasks_in"

# ---------------------------------------------------------------- never inside the toolchain
# F4 is exactly this: output written into a plugin's own tree. It is also pointless as well as
# wrong -- `/execute` refuses a plugin as a target (preflight.sh), so tasks generated in one
# could never be run.
for _pair in "tasks directory|${tasks_abs}" "target directory|${target_abs:-}"; do
    _what=${_pair%%|*}
    _path=${_pair#*|}
    [ -n "$_path" ] || continue
    if _root=$(plugin_root "$_path"); then
        refuse "$_what resolves inside a Claude Code plugin ($_root): $_path -- generated output must not be written into the toolchain"
    fi
done

# The echo item 4.6 asks for. A wrong target is then visible before a single file is written,
# rather than discovered afterwards in someone else's directory.
printf 'tasks_dir=%s\n' "$tasks_abs"
[ -n "${target_abs:-}" ] && printf 'target_dir=%s\n' "$target_abs"

exit 0
