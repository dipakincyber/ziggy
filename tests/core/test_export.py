from core.export import (
    ExportFormat,
    ExportRequest,
    ExportResult,
    ExportService,
    UnsupportedExportDataError,
)


def test_export_formats_exist():
    assert ExportFormat.JSON.value == "json"
    assert ExportFormat.CSV.value == "csv"
    assert ExportFormat.TEXT.value == "text"


def test_export_request_requires_valid_format():
    try:
        ExportRequest(
            format="json",
            data={"name": "ziggy"},
        )
        assert False
    except TypeError:
        pass


def test_export_request_is_immutable():
    request = ExportRequest(
        format=ExportFormat.JSON,
        data={"name": "ziggy"},
    )

    try:
        request.data = {}
        assert False
    except AttributeError:
        pass


def test_json_export():
    service = ExportService()

    result = service.json(
        {
            "name": "ziggy",
            "version": "1.0",
        }
    )

    assert result.format == ExportFormat.JSON
    assert result.content == (
        '{\n'
        '  "name": "ziggy",\n'
        '  "version": "1.0"\n'
        '}'
    )


def test_json_export_is_deterministic():
    service = ExportService()

    first = service.json(
        {
            "z": 1,
            "a": 2,
        }
    )

    second = service.json(
        {
            "a": 2,
            "z": 1,
        }
    )

    assert first.content == second.content


def test_json_export_supports_nested_data():
    service = ExportService()

    result = service.json(
        {
            "module": {
                "name": "security",
                "enabled": True,
            }
        }
    )

    assert '"module"' in result.content
    assert '"name": "security"' in result.content
    assert '"enabled": true' in result.content


def test_csv_export():
    service = ExportService()

    result = service.csv(
        [
            {"name": "security", "version": "1.0"},
            {"name": "network", "version": "2.0"},
        ]
    )

    assert result.format == ExportFormat.CSV
    assert result.content == (
        "name,version\n"
        "security,1.0\n"
        "network,2.0\n"
    )


def test_csv_headers_are_deterministic():
    service = ExportService()

    result = service.csv(
        [
            {"version": "1.0", "name": "security"},
        ]
    )

    assert result.content == (
        "name,version\n"
        "security,1.0\n"
    )


def test_csv_supports_missing_fields():
    service = ExportService()

    result = service.csv(
        [
            {"name": "security"},
            {"name": "network", "version": "2.0"},
        ]
    )

    assert result.content == (
        "name,version\n"
        "security,\n"
        "network,2.0\n"
    )


def test_csv_empty_sequence():
    service = ExportService()

    result = service.csv([])

    assert result.content == ""


def test_csv_rejects_non_sequence():
    service = ExportService()

    try:
        service.csv({"name": "security"})
        assert False
    except UnsupportedExportDataError:
        pass


def test_csv_rejects_non_mapping_rows():
    service = ExportService()

    try:
        service.csv(
            [
                {"name": "security"},
                "invalid row",
            ]
        )
        assert False
    except UnsupportedExportDataError:
        pass


def test_text_export_string():
    service = ExportService()

    result = service.text("Ziggy Core")

    assert result.format == ExportFormat.TEXT
    assert result.content == "Ziggy Core"


def test_text_export_mapping_is_deterministic():
    service = ExportService()

    result = service.text(
        {
            "version": "1.0",
            "name": "ziggy",
        }
    )

    assert result.content == (
        "name: ziggy\n"
        "version: 1.0"
    )


def test_text_export_sequence():
    service = ExportService()

    result = service.text(
        [
            "security",
            "network",
            "sandbox",
        ]
    )

    assert result.content == (
        "security\n"
        "network\n"
        "sandbox"
    )


def test_text_export_scalar():
    service = ExportService()

    result = service.text(42)

    assert result.content == "42"


def test_generic_export_dispatches_json():
    service = ExportService()

    request = ExportRequest(
        format=ExportFormat.JSON,
        data={"name": "ziggy"},
    )

    result = service.export(request)

    assert isinstance(result, ExportResult)
    assert result.format == ExportFormat.JSON
    assert '"name": "ziggy"' in result.content


def test_generic_export_dispatches_csv():
    service = ExportService()

    request = ExportRequest(
        format=ExportFormat.CSV,
        data=[
            {"name": "security"},
        ],
    )

    result = service.export(request)

    assert result.format == ExportFormat.CSV
    assert result.content == (
        "name\n"
        "security\n"
    )


def test_generic_export_dispatches_text():
    service = ExportService()

    request = ExportRequest(
        format=ExportFormat.TEXT,
        data="hello",
    )

    result = service.export(request)

    assert result.format == ExportFormat.TEXT
    assert result.content == "hello"


def test_generic_export_rejects_invalid_request():
    service = ExportService()

    try:
        service.export("invalid")
        assert False
    except TypeError:
        pass


def test_export_result_is_immutable():
    result = ExportResult(
        format=ExportFormat.TEXT,
        content="hello",
    )

    try:
        result.content = "changed"
        assert False
    except AttributeError:
        pass
