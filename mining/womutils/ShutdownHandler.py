"""
Implements a handler that catches interrupting signals, such as CTRL+C. Usage:

for obj in large_list:
    with ShutdownHandler() as shutdownHandler:
        try:
            doLongWork()
        except Exception as e:
            log.exception("...")
        if shutdownHandler.interrupted:
            interrupted = True
            break # Don't continue with the outer loop

NOTE: The caller IS RESPONSIBLE to really end the program!!!
"""

import logging
import signal
import sys

log = logging.getLogger(__name__)

# Inspired by:
# - https://github.com/scrapy/scrapy/blob/5360ba34bc345667f77a4d4256f15fd648e42e18/scrapy/utils/ossignal.py#L11
# - https://stackoverflow.com/a/1112350
# - https://stackoverflow.com/a/3774396
# - https://stackoverflow.com/a/10972804
# - https://www.baeldung.com/linux/sigint-and-other-termination-signals
# - https://docs.python.org/3/library/signal.html
# - https://learn.microsoft.com/de-de/windows/console/ctrl-c-and-ctrl-break-signals

class ShutdownHandler:
    """Installs a handler that intercepts shutdown signals, e.g. CTRL+C"""
    def __enter__(self):
        # Setup idle state
        self.interrupted = False
        self.exited = False

        # Save original signal handlers to re-register them later on exit
        self.original_sigint_handler = signal.getsignal(signal.SIGINT)
        self.original_sigterm_handler = signal.getsignal(signal.SIGTERM)
        if sys.platform == 'win32':
            # SIGBREAK is not available on unix-based systems
            self.original_sigbreak_handler = signal.getsignal(signal.SIGBREAK)

        # This methods actually handles the interrupting signal
        def handler(signum, frame):
            self.on_exit()
            # Set flag that the program was interrupted
            self.interrupted = True
            log.info(f"{signal.Signals(signum).name} received. Will exit gracefully.")
        
        # Register handler

        # On Unix, SIGINT is sent on STRG+C
        signal.signal(signal.SIGINT, handler)
        # SIGTERM is sent by 'kill' command
        signal.signal(signal.SIGTERM, handler)
        # On Windows, SIGBREAK is sent on STRG+C
        if sys.platform == 'win32':
            signal.signal(signal.SIGBREAK, handler)

        return self
    
    def __exit__(self, type, value, traceback):
        self.on_exit()
    
    def on_exit(self):
        if not self.exited:
            # Re-register previously assigned handlers
            # This makes it possible to press CTRL+C twice to _not_ shutdown gracefully
            signal.signal(signal.SIGINT, self.original_sigint_handler)
            signal.signal(signal.SIGTERM, self.original_sigterm_handler)
            if sys.platform == 'win32':
                # SIGBREAK is not available on unix-based systems
                signal.signal(signal.SIGBREAK, self.original_sigbreak_handler)
                
            # Set this handler as exited to prevent calling again and again
            self.exited = True
