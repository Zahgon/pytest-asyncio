"""pytest-asyncio implementation."""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import enum
import functools
import inspect
import socket
import sys
import traceback
import warnings
from asyncio import AbstractEventLoop
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Callable,
    Collection,
    Generator,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
)
from types import AsyncGeneratorType, CoroutineType
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    ParamSpec,
    TypeAlias,
    TypeVar,
    overload,
)

import pluggy
import pytest
from _pytest.fixtures import resolve_fixture_function
from _pytest.scope import Scope
from pytest import (
    Config,
    FixtureDef,
    FixtureRequest,
    Function,
    Item,
    Mark,
    MonkeyPatch,
    Parser,
    PytestCollectionWarning,
    PytestDeprecationWarning,
    PytestPluginManager,
)

if sys.version_info >= (3, 11):
    from asyncio import Runner
else:
    from backports.asyncio.runner import Runner

if sys.version_info >= (3, 13):
    from typing import TypeIs
else:
    from typing_extensions import TypeIs

if TYPE_CHECKING:
    # AbstractEventLoopPolicy is deprecated and scheduled for removal in Python 3.16
    # Import it for type checking only to avoid raising a DeprecationWarning.
    from asyncio import AbstractEventLoopPolicy

_ScopeName = Literal["session", "package", "module", "class", "function"]
_R = TypeVar("_R", bound=Awaitable[Any] | AsyncIterator[Any])
_P = ParamSpec("_P")
FixtureFunction = Callable[_P, _R]
LoopFactory: TypeAlias = Callable[[], AbstractEventLoop]


class PytestAsyncioError(Exception):
    """Base class for exceptions raised by pytest-asyncio"""


class Mode(str, enum.Enum):
    AUTO = "auto"
    STRICT = "strict"


hookspec = pluggy.HookspecMarker("pytest")


class PytestAsyncioSpecs:
    @hookspec(firstresult=True)
    def pytest_asyncio_loop_factories(
        self,
        config: Config,
        item: Item,
    ) -> Mapping[str, LoopFactory] | None:
        raise NotImplementedError  # pragma: no cover


ASYNCIO_MODE_HELP = """\
'auto' - for automatically handling all async functions by the plugin
'strict' - for autoprocessing disabling (useful if different async frameworks \
should be tested together, e.g. \
both pytest-asyncio and pytest-trio are used in the same project)
"""


def pytest_addoption(parser: Parser, pluginmanager: PytestPluginManager) -> None:
    pass


@overload
def fixture(
    fixture_function: FixtureFunction[_P, _R],
    *,
    scope: _ScopeName | Callable[[str, Config], _ScopeName] = ...,
    loop_scope: _ScopeName | None = ...,
    params: Iterable[object] | None = ...,
    autouse: bool = ...,
    ids: (
        Iterable[str | float | int | bool | None]
        | Callable[[Any], object | None]
        | None
    ) = ...,
    name: str | None = ...,
) -> FixtureFunction[_P, _R]: ...


@overload
def fixture(
    fixture_function: None = ...,
    *,
    scope: _ScopeName | Callable[[str, Config], _ScopeName] = ...,
    loop_scope: _ScopeName | None = ...,
    params: Iterable[object] | None = ...,
    autouse: bool = ...,
    ids: (
        Iterable[str | float | int | bool | None]
        | Callable[[Any], object | None]
        | None
    ) = ...,
    name: str | None = None,
) -> Callable[[FixtureFunction[_P, _R]], FixtureFunction[_P, _R]]: ...


def fixture(
    fixture_function: FixtureFunction[_P, _R] | None = None,
    loop_scope: _ScopeName | None = None,
    **kwargs: Any,
) -> (
    FixtureFunction[_P, _R]
    | Callable[[FixtureFunction[_P, _R]], FixtureFunction[_P, _R]]
):
    if fixture_function is not None:
        _make_asyncio_fixture_function(fixture_function, loop_scope)
        return pytest.fixture(fixture_function, **kwargs)

    else:

        @functools.wraps(fixture)
        def inner(fixture_function: FixtureFunction[_P, _R]) -> FixtureFunction[_P, _R]:
            pass

        return inner


def _is_asyncio_fixture_function(obj: Any) -> bool:
    pass


def _make_asyncio_fixture_function(obj: Any, loop_scope: _ScopeName | None) -> None:
    if hasattr(obj, "__func__"):
        # instance method, check the function object
        obj = obj.__func__
    obj._force_asyncio_fixture = True
    obj._loop_scope = loop_scope


def _is_coroutine_or_asyncgen(obj: Any) -> bool:
    pass


def _get_asyncio_mode(config: Config) -> Mode:
    pass


def _get_asyncio_debug(config: Config) -> bool:
    pass


_INVALID_LOOP_FACTORIES = """\
pytest_asyncio_loop_factories must return a non-empty mapping of \
factory names to callables.
"""


def _collect_hook_loop_factories(
    config: Config,
    item: Item,
) -> dict[str, LoopFactory] | None:
    pass


_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET = """\
The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the "fixture" caching \
scope. Future versions of pytest-asyncio will default the loop scope for asynchronous \
fixtures to "function" scope. Set the default fixture loop scope explicitly in order \
to avoid unexpected behavior in the future. Valid fixture loop scopes are: \
"function", "class", "module", "package", "session"
"""


def _validate_scope(scope: str | None, option_name: str) -> None:
    pass


def pytest_configure(config: Config) -> None:
    pass


@pytest.hookimpl(tryfirst=True)
def pytest_report_header(config: Config) -> list[str]:
    """Add asyncio config to pytest header."""
    pass


def _fixture_synchronizer(
    fixturedef: FixtureDef, runner: Runner, request: FixtureRequest
) -> Callable:
    """Returns a synchronous function evaluating the specified fixture."""
    pass


SyncGenFixtureParams = ParamSpec("SyncGenFixtureParams")
SyncGenFixtureYieldType = TypeVar("SyncGenFixtureYieldType")


def _wrap_syncgen_fixture(
    fixture_function: Callable[
        SyncGenFixtureParams, Generator[SyncGenFixtureYieldType]
    ],
    runner: Runner,
) -> Callable[SyncGenFixtureParams, Generator[SyncGenFixtureYieldType]]:
    @functools.wraps(fixture_function)
    def wrapper(*args, **kwargs):
        pass

    return wrapper


SyncFixtureParams = ParamSpec("SyncFixtureParams")
SyncFixtureReturnType = TypeVar("SyncFixtureReturnType")


def _wrap_sync_fixture(
    fixture_function: Callable[SyncFixtureParams, SyncFixtureReturnType],
    runner: Runner,
) -> Callable[SyncFixtureParams, SyncFixtureReturnType]:
    @functools.wraps(fixture_function)
    def wrapper(*args, **kwargs):
        pass

    return wrapper


AsyncGenFixtureParams = ParamSpec("AsyncGenFixtureParams")
AsyncGenFixtureYieldType = TypeVar("AsyncGenFixtureYieldType")


def _wrap_asyncgen_fixture(
    fixture_function: Callable[
        AsyncGenFixtureParams, AsyncGeneratorType[AsyncGenFixtureYieldType, Any]
    ],
    runner: Runner,
    request: FixtureRequest,
) -> Callable[AsyncGenFixtureParams, AsyncGenFixtureYieldType]:
    @functools.wraps(fixture_function)
    def wrapper(*args, **kwargs):
        pass

    return wrapper


AsyncFixtureParams = ParamSpec("AsyncFixtureParams")
AsyncFixtureReturnType = TypeVar("AsyncFixtureReturnType")


def _wrap_async_fixture(
    fixture_function: Callable[
        AsyncFixtureParams, CoroutineType[Any, Any, AsyncFixtureReturnType]
    ],
    runner: Runner,
    request: FixtureRequest,
) -> Callable[AsyncFixtureParams, AsyncFixtureReturnType]:
    @functools.wraps(fixture_function)
    def wrapper(*args, **kwargs):
        pass

    return wrapper


def _apply_contextvar_changes(
    context: contextvars.Context,
) -> Callable[[], None] | None:
    """
    Copy contextvar changes from the given context to the current context.

    If any contextvars were modified by the fixture, return a finalizer that
    will restore them.
    """
    pass


class PytestAsyncioFunction(Function):
    """Base class for all test functions managed by pytest-asyncio."""

    @classmethod
    def item_subclass_for(cls, item: Function, /) -> type[PytestAsyncioFunction] | None:
        """
        Returns a subclass of PytestAsyncioFunction if there is a specialized subclass
        for the specified function item.

        Return None if no specialized subclass exists for the specified item.
        """
        pass

    @classmethod
    def _from_function(cls, function: Function, /) -> Function:
        """
        Instantiates this specific PytestAsyncioFunction type from the specified
        Function item.
        """
        pass

    @staticmethod
    def _can_substitute(item: Function) -> bool:
        """Returns whether the specified function can be replaced by this class"""
        raise NotImplementedError()

    def setup(self) -> None:
        pass

    def runtest(self) -> None:
        pass

    @functools.cached_property
    def _loop_scope(self) -> _ScopeName:
        """
        Return the scope of the asyncio event loop this item is run in.

        The effective scope is determined lazily. It is identical to to the
        `loop_scope` value of the closest `asyncio` pytest marker. If no such
        marker is present, the the loop scope is determined by the configuration
        value of `asyncio_default_test_loop_scope`, instead.
        """
        pass

    @property
    def _synchronization_target_attr(self) -> tuple[object, str]:
        """
        Return the coroutine that needs to be synchronized during the test run.

        This method is intended to be overwritten by subclasses when they need to apply
        the coroutine synchronizer to a value that's different from self.obj
        e.g. the AsyncHypothesisTest subclass.
        """
        pass


class Coroutine(PytestAsyncioFunction):
    """Pytest item created by a coroutine"""

    @staticmethod
    def _can_substitute(item: Function) -> bool:
        pass


class AsyncGenerator(PytestAsyncioFunction):
    """Pytest item created by an asynchronous generator"""

    @staticmethod
    def _can_substitute(item: Function) -> bool:
        pass

    @classmethod
    def _from_function(cls, function: Function, /) -> Function:
        pass


class AsyncStaticMethod(PytestAsyncioFunction):
    """
    Pytest item that is a coroutine or an asynchronous generator
    decorated with staticmethod
    """

    @staticmethod
    def _can_substitute(item: Function) -> bool:
        pass


class AsyncHypothesisTest(PytestAsyncioFunction):
    """
    Pytest item that is coroutine or an asynchronous generator decorated by
    @hypothesis.given.
    """

    def setup(self) -> None:
        pass

    @staticmethod
    def _can_substitute(item: Function) -> bool:
        pass

    @property
    def _synchronization_target_attr(self) -> tuple[object, str]:
        pass


def _resolve_asyncio_marker(item: Function) -> Mark | None:
    pass


# The function name needs to start with "pytest_"
# see https://github.com/pytest-dev/pytest/issues/11307
@pytest.hookimpl(specname="pytest_pycollect_makeitem", hookwrapper=True)
def pytest_pycollect_makeitem_convert_async_functions_to_subclass(
    collector: pytest.Module | pytest.Class, name: str, obj: object
) -> Generator[None, pluggy.Result, None]:
    """
    Converts coroutines and async generators collected as pytest.Functions
    to AsyncFunction items.
    """
    pass


@pytest.hookimpl(tryfirst=True)
def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    pass


@contextlib.contextmanager
def _temporary_event_loop(loop: AbstractEventLoop) -> Iterator[None]:
    pass


@contextlib.contextmanager
def _temporary_event_loop_policy(
    policy: AbstractEventLoopPolicy,
    *,
    has_custom_factory: bool,
) -> Iterator[None]:
    pass


def _get_event_loop_policy() -> AbstractEventLoopPolicy:
    pass


def _set_event_loop_policy(policy: AbstractEventLoopPolicy) -> None:
    pass


def _get_event_loop_no_warn(
    policy: AbstractEventLoopPolicy | None = None,
) -> asyncio.AbstractEventLoop:
    pass


def _set_event_loop(loop: AbstractEventLoop | None) -> None:
    pass


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem: Function) -> object | None:
    """Pytest hook called before a test case is run."""
    pass


def _synchronize_coroutine(
    func: Callable[..., CoroutineType],
    runner: asyncio.Runner,
    context: contextvars.Context,
):
    """
    Return a sync wrapper around a coroutine executing it in the
    specified runner and context.
    """
    pass


@pytest.hookimpl(wrapper=True)
def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
    pass


_DUPLICATE_LOOP_SCOPE_DEFINITION_ERROR = """\
An asyncio pytest marker defines both "scope" and "loop_scope", \
but it should only use "loop_scope".
"""

_MARKER_SCOPE_KWARG_DEPRECATION_WARNING = """\
The "scope" keyword argument to the asyncio marker has been deprecated. \
Please use the "loop_scope" argument instead.
"""

_INVALID_LOOP_FACTORIES_KWARG = """\
mark.asyncio 'loop_factories' must be a non-empty sequence of strings.
"""


def _parse_asyncio_marker(
    asyncio_marker: Mark,
) -> tuple[_ScopeName | None, Sequence[str] | None]:
    pass


def _validate_asyncio_marker(asyncio_marker: Mark) -> None:
    pass


def _get_default_test_loop_scope(config: Config) -> Any:
    pass


_RUNNER_TEARDOWN_WARNING = """\
An exception occurred during teardown of an asyncio.Runner. \
The reason is likely that you closed the underlying event loop in a test, \
which prevents the cleanup of asynchronous generators by the runner.
This warning will become an error in future versions of pytest-asyncio. \
Please ensure that your tests don't close the event loop. \
Here is the traceback of the exception triggered during teardown:
%s
"""


def _create_scoped_runner_fixture(scope: _ScopeName) -> Callable:
    @pytest.fixture(
        scope=scope,
        name=f"_{scope}_scoped_runner",
    )
    def scoped_runner(*args, **kwargs):
        pass

    return scoped_runner


for scope in Scope:
    globals()[f"_{scope.value}_scoped_runner"] = _create_scoped_runner_fixture(
        scope.value
    )


@pytest.fixture(scope="session")
def _asyncio_loop_factory(request: FixtureRequest) -> LoopFactory | None:
    pass


@pytest.fixture(scope="session", autouse=True)
def event_loop_policy() -> AbstractEventLoopPolicy:
    """Return an instance of the policy used to create asyncio event loops."""
    pass


def is_async_test(item: Item) -> TypeIs[PytestAsyncioFunction]:
    """Returns whether a test item is a pytest-asyncio test"""
    return isinstance(item, PytestAsyncioFunction)


def _unused_port(socket_type: int) -> int:
    """Find an unused localhost port from 1024-65535 and return it."""
    pass


@pytest.fixture
def unused_tcp_port() -> int:
    pass


@pytest.fixture
def unused_udp_port() -> int:
    pass


@pytest.fixture(scope="session")
def unused_tcp_port_factory() -> Callable[[], int]:
    """A factory function, producing different unused TCP ports."""
    pass


@pytest.fixture(scope="session")
def unused_udp_port_factory() -> Callable[[], int]:
    """A factory function, producing different unused UDP ports."""
    pass
