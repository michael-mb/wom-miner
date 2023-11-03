import logging
from time import perf_counter

log = logging.getLogger(__name__)


def toCoarseReadableTime(seconds:int) -> str:
    """Returns seconds/minutes/hours of the passed seconds value"""
    if seconds <= 60:
        return str(round(seconds)) + "s"
    elif seconds <= 3600:
        return str(round(seconds / 60)) + "min"
    else:
        return str(round(seconds / 3600)) + "h"


def toFineReadableTime(seconds:int) -> str:
    """Returns seconds, minutes and hours of the passed seconds value"""
    if seconds <= 60:
        return str(round(seconds)) + "s"
    elif seconds <= 3600:
        min, sec = divmod(seconds, 60)
        return f"{min:.0f}min {sec:.0f}s"
    else:
        min, sec = divmod(seconds, 60)
        h, min = divmod(min, 60)
        return f"{h:.0f}h {min:.0f}min {sec:.0f}s"


class Progress:
    """Logs the progress of a long-running loop"""

    def __init__(self, total:int, frequency:int) -> None:
        """Inits the logger with a total amount of documents and a number after how many runs is logged."""
        self.total = total
        self.start = perf_counter()
        self.frequency = frequency
        self.processed = 0
        self.ignored = 0
        log.info(f"{total} documents will be processed")
    
    def next(self):
        """Increments the counter and logs if necessary"""
        self.processed += 1

        if self.processed % self.frequency == 0:
            diff = perf_counter() - self.start
            # Estimate the remaining time based on processed documents since start and the time gone by
            remaining = self.total - self.processed
            docs_per_minute = round((self.processed / diff) * 60)
            estimation = toCoarseReadableTime((diff/self.processed) * remaining)
            log.info(f"Processed {self.processed} documents in {toFineReadableTime(diff)} ({docs_per_minute} per minute), ignored {self.ignored} ({round((self.ignored / self.processed)*100,2)}%), {remaining} remaining (~{estimation})")
    
    def ignore(self):
        """Increments the counter for ignored documents"""
        self.ignored += 1
    
    def finish(self):
        """Logs the total time"""
        diff = perf_counter() - self.start
        docs_per_minute = round((self.processed / diff) * 60)
        log.info(f"Processed {self.processed} documents in {toFineReadableTime(diff)} ({docs_per_minute}/minute), ignored {self.ignored} ({round((self.ignored / self.processed)*100,2)}%)")