from dataclasses import dataclass, field


@dataclass
class HRGraphFrame:
    timestamps : list[float] = field(default_factory=list)
    graph_values : list[float] = field(default_factory=list)