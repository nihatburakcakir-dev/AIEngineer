"""Small repeatable benchmark helpers; they never make a cloud request."""

from dataclasses import asdict, dataclass
from time import perf_counter


@dataclass(frozen=True)
class LocalBenchmarkResult:
    task: str
    model: str
    success: bool
    elapsed_seconds: float
    detail: str

    def to_dict(self):
        return asdict(self)


class LocalBenchmark:
    def text(self, client, task="planning", prompt="Reply with exactly: LOCAL_BENCHMARK_OK"):
        started = perf_counter()
        try:
            response = client.generate(prompt, task=task)
            return LocalBenchmarkResult(task, client.model, bool(response.strip()), perf_counter() - started, response.strip())
        except Exception as error:
            return LocalBenchmarkResult(task, client.model, False, perf_counter() - started, str(error))

    def vision(self, client, image_path):
        started = perf_counter()
        try:
            analysis = client.analyze(image_path)
            detail = f"camera={analysis.camera.angle}; dimension={analysis.assets.dimension}; ui={len(analysis.ui)}"
            return LocalBenchmarkResult("vision", client.model, True, perf_counter() - started, detail)
        except Exception as error:
            return LocalBenchmarkResult("vision", client.model, False, perf_counter() - started, str(error))
