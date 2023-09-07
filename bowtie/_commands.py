"""
Hand crafted classes which should undoubtedly be autogenerated from the schema.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, TypeVar, cast

try:
    from typing import dataclass_transform
except ImportError:
    from typing_extensions import dataclass_transform

import json

from attrs import asdict, field, frozen

from bowtie import exceptions

if TYPE_CHECKING:
    from bowtie import _report


@frozen
class Test:
    description: str
    instance: Any
    comment: str | None = None
    valid: bool | None = None


@frozen
class TestCase:
    description: str
    schema: Any
    tests: list[Test]
    comment: str | None = None
    registry: dict[str, Any] | None = None

    @classmethod
    def from_dict(
        cls,
        tests: Iterable[dict[str, Any]],
        **kwargs: Any,
    ) -> TestCase:
        kwargs["tests"] = [Test(**test) for test in tests]
        return cls(**kwargs)

    def without_expected_results(self) -> dict[str, Any]:
        as_dict = {
            "tests": [
                asdict(
                    test,
                    filter=lambda k, v: k.name != "valid"
                    and (k.name != "comment" or v is not None),
                )
                for test in self.tests
            ],
        }
        as_dict.update(
            asdict(
                self,
                filter=lambda k, v: k.name != "tests"
                and (k.name not in {"comment", "registry"} or v is not None),
            ),
        )
        return as_dict


@frozen
class Started:
    implementation: dict[str, Any]
    ready: bool = field()
    version: int = field()

    @ready.validator  # type: ignore[reportGeneralTypeIssues]
    def _check_ready(self, _: Any, ready: bool):
        if not ready:
            raise exceptions.ImplementationNotReady()

    @version.validator  # type: ignore[reportGeneralTypeIssues]
    def _check_version(self, _: Any, version: int):
        if version != 1:
            raise exceptions.VersionMismatch(expected=1, got=version)


_R = TypeVar("_R", covariant=True)


class Command(Protocol[_R]):
    def to_request(self, validate: Callable[..., None]) -> dict[str, Any]:
        ...

    @staticmethod
    def from_response(
        response: bytes,
        validate: Callable[..., None],
    ) -> _R | None:
        ...


@dataclass_transform()
def command(
    name: str,
    Response: Callable[..., _R | None],
) -> Callable[[type], type[Command[_R]]]:
    uri = f"https://bowtie.report/io-schema/{name}/"
    request_schema = {"$ref": uri}
    response_schema = {"$ref": f"{uri}response/"}

    def _command(cls: type) -> type[Command[_R]]:
        def to_request(
            self: Command[_R],
            validate: Callable[..., None],
        ) -> dict[str, Any]:
            request = dict(cmd=name, **asdict(self))
            validate(instance=request, schema=request_schema)
            return request

        @staticmethod
        def from_response(
            response: bytes,
            validate: Callable[..., None],
        ) -> _R | None:
            try:
                instance = json.loads(response)
            except json.JSONDecodeError as error:
                raise exceptions._ProtocolError(errors=[error])  # type: ignore[reportPrivateUsage]  # noqa: E501
            validate(instance=instance, schema=response_schema)
            return Response(**instance)

        cls = cast(type[Command[_R]], cls)
        cls.to_request = to_request
        cls.from_response = from_response
        return frozen(cls)

    return _command


@command(name="start", Response=Started)
class Start:
    version: int


START_V1 = Start(version=1)


@frozen
class StartedDialect:
    ok: bool

    OK: ClassVar[StartedDialect]


StartedDialect.OK = StartedDialect(ok=True)


@command(name="dialect", Response=StartedDialect)
class Dialect:
    dialect: str


def _case_result(
    errored: bool = False,
    skipped: bool = False,
    **response: Any,
) -> Callable[[str, bool | None], CaseResult | CaseSkipped | CaseErrored]:
    if errored:
        return lambda implementation, expected: CaseErrored(
            implementation=implementation,
            **response,
        )
    elif skipped:
        return lambda implementation, expected: CaseSkipped(
            implementation=implementation,
            **response,
        )
    return lambda implementation, expected: CaseResult.from_dict(
        response,
        implementation=implementation,
        expected=expected,
    )


@frozen
class TestResult:
    errored = False
    skipped = False

    valid: bool

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> TestResult | SkippedTest | ErroredTest:
        if data.pop("skipped", False):
            return SkippedTest(**data)
        elif data.pop("errored", False):
            return ErroredTest(**data)
        return cls(valid=data["valid"])


@frozen
class SkippedTest:
    message: str | None = field(default=None)
    issue_url: str | None = field(default=None)

    errored = False
    skipped: bool = field(init=False, default=True)

    @property
    def reason(self) -> str:
        if self.message is not None:
            return self.message
        if self.issue_url is not None:
            return self.issue_url
        return "skipped"


@frozen
class ErroredTest:
    context: dict[str, Any] = field(factory=dict)

    errored: bool = field(init=False, default=True)
    skipped: bool = False

    @property
    def reason(self) -> str:
        message = self.context.get("message")
        if message:
            return message
        return "Encountered an error."


class ReportableResult(Protocol):
    errored: bool
    failed: bool

    def report(self, reporter: _report._CaseReporter) -> None:  # type: ignore[reportPrivateUsage]  # noqa: E501
        pass


@frozen
class CaseResult:
    errored = False

    implementation: str
    seq: int
    results: list[TestResult | SkippedTest | ErroredTest]
    expected: list[bool | None]

    @classmethod
    def from_dict(cls, data: Any, **kwargs: Any) -> CaseResult:
        return cls(
            results=[TestResult.from_dict(t) for t in data.pop("results")],
            **data,
            **kwargs,
        )

    @property
    def failed(self) -> bool:
        return any(failed for _, failed in self.compare())

    def report(self, reporter: _report._CaseReporter) -> None:  # type: ignore[reportPrivateUsage]  # noqa: E501
        reporter.got_results(self)

    def compare(
        self,
    ) -> Iterable[tuple[TestResult | SkippedTest | ErroredTest, bool]]:
        for test, expected in zip(self.results, self.expected):
            failed: bool = (  # type: ignore[reportUnknownVariableType]
                not test.skipped
                and not test.errored
                and expected is not None
                and expected != test.valid  # type: ignore[reportUnknownMemberType]  # noqa: E501
            )
            yield test, failed


@frozen
class CaseErrored:
    """
    A full test case errored.
    """

    errored = True
    failed = False

    implementation: str
    seq: int
    context: dict[str, Any]

    caught: bool = True

    def report(self, reporter: _report._CaseReporter):  # type: ignore[reportPrivateUsage]  # noqa: E501
        reporter.errored(self)

    @classmethod
    def uncaught(
        cls,
        implementation: str,
        seq: int,
        **context: Any,
    ) -> CaseErrored:
        return cls(
            implementation=implementation,
            seq=seq,
            caught=False,
            context=context,
        )


@frozen
class CaseSkipped:
    """
    A full test case was skipped.
    """

    errored = False
    failed = False

    implementation: str
    seq: int

    message: str | None = None
    issue_url: str | None = None
    skipped: bool = field(init=False, default=True)

    def report(self, reporter: _report._CaseReporter):  # type: ignore[reportPrivateUsage]  # noqa: E501
        reporter.skipped(self)


@frozen
class Empty:
    """
    An implementation didn't send a response.
    """

    errored = True
    failed = False

    implementation: str

    def report(self, reporter: _report._CaseReporter):  # type: ignore[reportPrivateUsage]  # noqa: E501
        reporter.no_response(implementation=self.implementation)


@command(name="run", Response=_case_result)
class Run:
    seq: int
    case: dict[str, Any]


@command(name="stop", Response=lambda: None)
class Stop:
    pass


STOP = Stop()
