from dataclasses import dataclass, field
import numpy as np


@dataclass
class EEGGraphFrame:
    timestamps : list[float] = field(default_factory=list)
    fft_values_buffer : list[float] = field(default_factory=list)
    frequencies : list[float] = field(default_factory=list)
    fft_vizualizer_values : list[list[float]] = field(default_factory=list)
    fft_timestamps : list[float] = field(default_factory=list)
    colors : list[list[int]] = field(default_factory=list)