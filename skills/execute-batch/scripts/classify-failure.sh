#!/usr/bin/env sh
# Decide whether a failed task may be retried, or whether the run must stop instead.
#
# `execute-task` retries five times. Against a subscription window that will not reopen for
# hours, that is five guaranteed failures burning the allowance that a resume will need. The
# retry loop cannot tell the difference between "the tests failed" and "the account is out of
# usage" -- both arrive as an error string -- so something has to look at the string.
#
# That something is this script and not a paragraph in SKILL.md, for the reason F15 recorded:
# prose guards are weighed, and a capable model weighing "the API returned a usage limit" will
# reason its way to one more attempt. An exit code cannot be reasoned with.
#
# Usage:
#   classify-failure.sh <error-file>
#   ... | classify-failure.sh
#
# stdout, first line: one of `limit`, `transient`, `code`
#         further lines, when `limit`: what matched, and any reset time found in the text
#
# exit 0: retry this task. Ordinary code failure, or a transient API blip.
# exit 3: STOP the run. Do not retry this task, and do not consume one of its five attempts.
# exit 2: bad usage.
#
# THREE CLASSES, BECAUSE TWO WOULD BE WRONG
#
# `transient` exists so the stop stays precise. A per-minute 429 and an overloaded 529 read
# textually like limits but are nothing of the kind -- the window has not closed and the next
# attempt may well succeed. Collapsing them into `limit` would halt healthy runs on a blip.
# `transient` and `code` behave identically today (retry, consume an attempt, bounded by the
# five-attempt cap); the class is reported so a run that failed on infrastructure does not
# read as a run that failed on its own code.
#
# WHICH WAY IT FAILS WHEN IT IS UNSURE
#
# Anything unrecognised is `code`, which retries -- exactly what happens today. The guard can
# therefore only improve on current behaviour, never make it worse. That is deliberate: the
# alternative default would let an unfamiliar error message halt a working pipeline.
#
# The opposite error -- calling a code failure a limit -- stops the run early. That is benign
# by construction: the ledger is verified against git, so the operator loses nothing but time
# and resumes. It is still worth avoiding, which is why every `limit` pattern below is a
# specific multi-word phrase rather than a keyword.
#
# PASS THE ERROR, NOT THE LOG
#
# Feed this the failure text -- the agent's `error` object, or the exception the Task tool
# returned. A whole test log is the wrong input: a project whose own tests exercise rate
# limiting will contain these phrases as fixture data, and the classifier cannot tell a
# quoted error from a real one.

set -eu

if [ $# -gt 1 ]; then
    echo "usage: $0 [<error-file>]" >&2
    exit 2
fi

if [ $# -eq 1 ]; then
    [ -f "$1" ] || { echo "no such file: $1" >&2; exit 2; }
    text=$(cat -- "$1")
else
    text=$(cat)
fi

# The window is closed or the account is out of allowance. Nothing gets better by trying again.
# Built by concatenation rather than one long line: inside single quotes a trailing backslash
# is a literal backslash, not a continuation, so a "wrapped" pattern would be a broken one.
LIMIT='usage limit reached|claude (ai )?usage limit|(5|five)[ -]?hour limit'
LIMIT="$LIMIT|weekly limit|limit (has been |was )?reached"
LIMIT="$LIMIT|quota (has been |was )?exceeded|exceeded your [a-z ]*quota|insufficient_quota"
LIMIT="$LIMIT|credit balance is too low|upgrade to increase your usage"
LIMIT="$LIMIT|out of (usage|credits)|plan limit reached|subscription limit"

# The service hiccuped. The window is fine; the next attempt may succeed.
TRANSIENT='rate_limit_error|\b429\b|overloaded_error|\b529\b|internal server error'
TRANSIENT="$TRANSIENT|service unavailable|bad gateway|gateway timeout"
TRANSIENT="$TRANSIENT|connection (error|reset|refused)|econnreset|etimedout"
TRANSIENT="$TRANSIENT|socket hang up|request timed out|\b50[023]\b"

matches() {
    printf '%s' "$text" | grep -qiE "$1"
}

if matches "$LIMIT"; then
    printf 'limit\n'
    printf '%s\n' "$text" | grep -oiE "$LIMIT" | head -1 | sed 's/^/matched: /'
    # The stop message is only useful if it says when the operator may resume. Take a reset
    # time straight out of the error text when one is there; say nothing when it is not,
    # rather than inventing one.
    reset=$(printf '%s' "$text" \
            | grep -oiE '(resets?|resets at|available again|try again)[ a-z]{0,12}[0-9][^."]{0,40}' \
            | head -1) || reset=''
    [ -n "$reset" ] && printf 'reset: %s\n' "$reset"
    exit 3
fi

if matches "$TRANSIENT"; then
    printf 'transient\n'
    exit 0
fi

printf 'code\n'
exit 0
