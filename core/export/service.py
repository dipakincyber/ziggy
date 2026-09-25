import csv
import io
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    TEXT = "text"


@dataclass(frozen=True)
class ExportRequest:
    format: ExportFormat
    data: Any

    def __post_init__(self) -> None:
        if not isinstance(self.format, ExportFormat):
            raise TypeError("format must be an ExportFormat")


@dataclass(frozen=True)
class ExportResult:
    format: ExportFormat
    content: str


class ExportError(Exception):
    pass


class UnsupportedExportDataError(ExportError):
    pass


class ExportService:
    def export(self, request: ExportRequest) -> ExportResult:
        if not isinstance(request, ExportRequest):
            raise TypeError("request must be an ExportRequest")

        if request.format == ExportFormat.JSON:
            content = self._export_json(request.data)
        elif request.format == ExportFormat.CSV:
            content = self._export_csv(request.data)
        elif request.format == ExportFormat.TEXT:
            content = self._export_text(request.data)
        else:
            raise ExportError("unsupported export format")

        return ExportResult(
            format=request.format,
            content=content,
        )

    def json(self, data: Any) -> ExportResult:
        return self.export(
            ExportRequest(
                format=ExportFormat.JSON,
                data=data,
            )
        )

    def csv(self, data: Any) -> ExportResult:
        return self.export(
            ExportRequest(
                format=ExportFormat.CSV,
                data=data,
            )
        )

    def text(self, data: Any) -> ExportResult:
        return self.export(
            ExportRequest(
                format=ExportFormat.TEXT,
                data=data,
            )
        )

    @staticmethod
    def _export_json(data: Any) -> str:
        try:
            return json.dumps(
                data,
                sort_keys=True,
                indent=2,
                default=str,
            )
        except (TypeError, ValueError) as exc:
            raise UnsupportedExportDataError(
                "data cannot be exported as JSON"
            ) from exc

    @staticmethod
    def _export_csv(data: Any) -> str:
        if not isinstance(data, (list, tuple)):
            raise UnsupportedExportDataError(
                "CSV export requires a sequence of mappings"
            )

        if not data:
            return ""

        if not all(isinstance(row, Mapping) for row in data):
            raise UnsupportedExportDataError(
                "CSV export requires a sequence of mappings"
            )

        fieldnames = sorted(
            {
                key
                for row in data
                for key in row.keys()
            },
            key=str,
        )

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )

        writer.writeheader()

        for row in data:
            writer.writerow(
                {
                    key: row.get(key, "")
                    for key in fieldnames
                }
            )

        return output.getvalue()

    @staticmethod
    def _export_text(data: Any) -> str:
        if isinstance(data, str):
            return data

        if isinstance(data, Mapping):
            return "\n".join(
                f"{key}: {data[key]}"
                for key in sorted(data.keys(), key=str)
            )

        if isinstance(data, (list, tuple)):
            return "\n".join(
                str(item)
                for item in data
            )

        return str(data)
