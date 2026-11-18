from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Record:
    date: str
    text: str
    page: int | None = None

    def as_dict(self):
        return asdict(self)
