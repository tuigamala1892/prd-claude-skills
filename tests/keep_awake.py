"""Stop the machine sleeping while a long run is in progress (Windows; no-op elsewhere).

Extracted from `fixture/run_5_2.py`, which had the only copy. That copy was written after a
run-10 resume was suspended 23:24 to 08:13 -- and the same thing then happened to a mutation
round on the night of 2026-08-26, because the fix lived in one caller rather than in a place
every long-running harness could reach.

**A suspended process gets no chance to act on a wall-clock deadline**, so a harness timeout
does not fire either: the run neither finishes nor fails, it simply stops existing until
someone moves the mouse. That is the failure mode this guards, and it is worse than a crash
because nothing reports it.

Use it around anything that runs for more than a minute or two:

    from keep_awake import keep_awake

    with keep_awake():
        ...
"""

import sys


class keep_awake:
    """Stop the machine sleeping while a run is in progress (Windows; no-op elsewhere).

    A run 10 resume was suspended from 23:24 to 08:13 because the machine slept overnight.
    Nothing was lost -- the process resumed and the ledger stayed consistent -- but a
    2-hour run occupied 10 hours of wall clock, and the harness's own timeout never fired,
    because a suspended process gets no chance to act on a wall-clock deadline.

    Deliberately *not* ES_DISPLAY_REQUIRED: the screen may sleep, only the system must
    stay up. SetThreadExecutionState is per-thread state and this harness is
    single-threaded, so setting it here covers the whole run.

    Confirmed working at the OS level: `powercfg /requests` from an elevated prompt lists
    python.exe under SYSTEM while a run is in progress. (That command needs administrator
    rights, so the harness itself can only check the API's return value.)
    """

    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __enter__(self):
        self.held = False
        if sys.platform != "win32":
            return self
        try:
            import ctypes
            self._k32 = ctypes.windll.kernel32
            # Returns the previous state, or 0 on failure.
            if self._k32.SetThreadExecutionState(self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED):
                self.held = True
                print("  (sleep inhibited for the duration of this run)", flush=True)
            else:
                print("  (WARNING: could not inhibit sleep; a long run may be suspended)",
                      flush=True)
        except Exception as e:
            print(f"  (WARNING: could not inhibit sleep: {e})", flush=True)
        return self

    def __exit__(self, *_exc):
        # Always release, including on Ctrl-C or an exception. Leaving the flag set would
        # keep the machine awake indefinitely after the harness exits.
        if self.held:
            try:
                self._k32.SetThreadExecutionState(self.ES_CONTINUOUS)
            except Exception:
                pass
        return False
