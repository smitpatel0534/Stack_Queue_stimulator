"""Operation history: records, filtering, search, statistics and CSV export."""
from __future__ import annotations

import csv
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, Iterable, List, Optional, Tuple, Union

CSV_HEADER = ("Number", "Data Structure", "Operation", "Value", "Status", "Details", "Timestamp")


@dataclass(frozen=True)
class OperationRecord:
    number: int
    structure: str
    operation: str
    value: str
    success: bool
    message: str
    timestamp: datetime

    @property
    def status(self) -> str:
        return "Success" if self.success else "Failed"

    @property
    def time_text(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def as_row(self) -> Tuple[str, str, str, str, str, str, str]:
        return (str(self.number), self.structure, self.operation, self.value,
                self.status, self.message, self.time_text)


class HistoryManager:
    """Keeps recent records plus running totals.

    Totals are independent of how many rows are displayed or stored, so the
    dashboard statistics stay accurate when the display limit is small.
    """

    def __init__(self, max_records: int = 5000) -> None:
        if max_records < 1:
            raise ValueError("max_records must be at least 1.")
        self._records: Deque[OperationRecord] = deque(maxlen=max_records)
        self._total = 0
        self._successful = 0
        self._failed = 0

    # -- statistics ----------------------------------------------------
    @property
    def total_operations(self) -> int:
        return self._total

    @property
    def successful_operations(self) -> int:
        return self._successful

    @property
    def failed_operations(self) -> int:
        return self._failed

    def __len__(self) -> int:
        """Number of records currently stored (not the lifetime total)."""
        return len(self._records)

    # -- recording -----------------------------------------------------
    def add(self, structure: str, operation: str, value: str = "", success: bool = True,
            message: str = "", timestamp: Optional[datetime] = None) -> OperationRecord:
        self._total += 1
        if success:
            self._successful += 1
        else:
            self._failed += 1
        record = OperationRecord(self._total, structure, operation, value, success, message,
                                 timestamp or datetime.now())
        self._records.append(record)
        return record

    def clear(self) -> None:
        """Forget all records and reset the statistics (does not touch any data structure)."""
        self._records.clear()
        self._total = self._successful = self._failed = 0

    # -- querying ------------------------------------------------------
    def query(self, structure: Optional[str] = None, operation: Optional[str] = None,
              search: Optional[str] = None, limit: Optional[int] = None) -> List[OperationRecord]:
        """Matching records, newest first, optionally truncated to ``limit``."""
        needle = (search or "").strip().lower()
        matches: List[OperationRecord] = []
        for record in reversed(self._records):
            if structure and record.structure != structure:
                continue
            if operation and record.operation != operation:
                continue
            if needle and needle not in " ".join(record.as_row()).lower():
                continue
            matches.append(record)
            if limit is not None and len(matches) >= limit:
                break
        return matches

    def recent(self, count: int) -> List[OperationRecord]:
        return self.query(limit=count)

    # -- export --------------------------------------------------------
    def export_csv(self, path: Union[str, Path], records: Optional[Iterable[OperationRecord]] = None) -> int:
        """Write records (default: all stored, oldest first) to ``path``. Returns the row count."""
        rows = list(records) if records is not None else list(self._records)
        with open(path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(CSV_HEADER)
            for record in rows:
                writer.writerow(record.as_row())
        return len(rows)
