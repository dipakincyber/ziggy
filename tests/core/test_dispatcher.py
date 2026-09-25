import pytest

from core.dispatch.dispatcher import (
    CommandDispatcher,
    DispatchError,
    DispatchRequest,
    DispatchResult,
)


def test_dispatch_request_stores_command():
    request = DispatchRequest(command="scan")

    assert request.command == "scan"
    assert request.arguments == ()
    assert request.options is None


def test_dispatch_request_stores_arguments_and_options():
    request = DispatchRequest(
        command="scan",
        arguments=("file.txt",),
        options={"local": True},
    )

    assert request.arguments == ("file.txt",)
    assert request.options == {"local": True}


@pytest.mark.parametrize(
    "command",
    [
        "",
        "scan file",
        "scan\tfile",
        "scan/file",
        "scan\\file",
    ],
)
def test_dispatch_request_validates_command(command):
    with pytest.raises(ValueError):
        DispatchRequest(command=command)


def test_dispatch_request_requires_tuple_arguments():
    with pytest.raises(TypeError):
        DispatchRequest(
            command="scan",
            arguments=["file.txt"],
        )


def test_dispatch_request_requires_dictionary_options():
    with pytest.raises(TypeError):
        DispatchRequest(
            command="scan",
            options=["local"],
        )


def test_dispatcher_starts_empty():
    dispatcher = CommandDispatcher()

    assert dispatcher.count() == 0
    assert not dispatcher.contains("scan")


def test_bind_registers_handler():
    dispatcher = CommandDispatcher()

    def handler():
        return "scanned"

    dispatcher.bind("scan", handler)

    assert dispatcher.count() == 1
    assert dispatcher.contains("scan")


def test_bind_requires_callable_handler():
    dispatcher = CommandDispatcher()

    with pytest.raises(TypeError):
        dispatcher.bind("scan", "not-a-handler")


def test_bind_rejects_duplicate_command():
    dispatcher = CommandDispatcher()

    def handler():
        return "scanned"

    dispatcher.bind("scan", handler)

    with pytest.raises(DispatchError):
        dispatcher.bind("scan", handler)

    assert dispatcher.count() == 1


@pytest.mark.parametrize(
    "command",
    [
        "",
        "scan file",
        "scan\tfile",
        "scan/file",
        "scan\\file",
    ],
)
def test_bind_validates_command(command):
    dispatcher = CommandDispatcher()

    with pytest.raises(ValueError):
        dispatcher.bind(command, lambda: None)


def test_dispatch_executes_bound_handler():
    dispatcher = CommandDispatcher()

    def handler():
        return "scan complete"

    dispatcher.bind("scan", handler)

    result = dispatcher.dispatch(
        DispatchRequest(command="scan")
    )

    assert isinstance(result, DispatchResult)
    assert result.command == "scan"
    assert result.value == "scan complete"


def test_dispatch_passes_positional_arguments():
    dispatcher = CommandDispatcher()

    def handler(path):
        return f"scanned:{path}"

    dispatcher.bind("scan", handler)

    result = dispatcher.dispatch(
        DispatchRequest(
            command="scan",
            arguments=("file.txt",),
        )
    )

    assert result.value == "scanned:file.txt"


def test_dispatch_passes_keyword_options():
    dispatcher = CommandDispatcher()

    def handler(local=False):
        return local

    dispatcher.bind("scan", handler)

    result = dispatcher.dispatch(
        DispatchRequest(
            command="scan",
            options={"local": True},
        )
    )

    assert result.value is True


def test_dispatch_passes_arguments_and_options_together():
    dispatcher = CommandDispatcher()

    def handler(path, local=False):
        return f"{path}:{local}"

    dispatcher.bind("scan", handler)

    result = dispatcher.dispatch(
        DispatchRequest(
            command="scan",
            arguments=("file.txt",),
            options={"local": True},
        )
    )

    assert result.value == "file.txt:True"


def test_dispatch_missing_handler_raises():
    dispatcher = CommandDispatcher()

    with pytest.raises(DispatchError):
        dispatcher.dispatch(
            DispatchRequest(command="scan")
        )


def test_dispatch_does_not_mutate_request_options():
    dispatcher = CommandDispatcher()

    received = {}

    def handler(**options):
        received.update(options)
        return "done"

    dispatcher.bind("scan", handler)

    options = {"local": True}
    request = DispatchRequest(
        command="scan",
        options=options,
    )

    dispatcher.dispatch(request)

    assert options == {"local": True}
    assert request.options == {"local": True}
    assert received == {"local": True}


def test_unbind_removes_handler():
    dispatcher = CommandDispatcher()

    dispatcher.bind("scan", lambda: "done")
    dispatcher.unbind("scan")

    assert dispatcher.count() == 0
    assert not dispatcher.contains("scan")


def test_unbind_missing_handler_raises():
    dispatcher = CommandDispatcher()

    with pytest.raises(DispatchError):
        dispatcher.unbind("scan")


def test_dispatcher_supports_multiple_commands():
    dispatcher = CommandDispatcher()

    dispatcher.bind("scan", lambda: "scan")
    dispatcher.bind("track", lambda: "track")

    assert dispatcher.count() == 2

    assert dispatcher.dispatch(
        DispatchRequest(command="scan")
    ).value == "scan"

    assert dispatcher.dispatch(
        DispatchRequest(command="track")
    ).value == "track"


def test_dispatch_result_is_immutable():
    dispatcher = CommandDispatcher()
    dispatcher.bind("scan", lambda: "done")

    result = dispatcher.dispatch(
        DispatchRequest(command="scan")
    )

    with pytest.raises(AttributeError):
        result.command = "other"
