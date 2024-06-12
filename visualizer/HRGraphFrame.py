from dataclasses import dataclass, field

@dataclass
class BioVariableGraphSettings:
    max : float = field(default=0.0)
    below_max_count : int = field(default=0)

@dataclass
class HRGraphFrame:
    timestamps_bpm : list[float] = field(default_factory=list)
    timestamps_rmssd : list[float] = field(default_factory=list)
    timestamps_sdnn : list[float] = field(default_factory=list)
    timestamps_poi_rat : list[float] = field(default_factory=list)
    bpm_values : list[float] = field(default_factory=list)
    rmssd_values : list[float] = field(default_factory=list)
    sdnn_values : list[float] = field(default_factory=list)
    poi_rat_values : list[float] = field(default_factory=list)
    bpm_settings : BioVariableGraphSettings = field(default_factory=BioVariableGraphSettings)
    rmssd_settings : BioVariableGraphSettings = field(default_factory=BioVariableGraphSettings)
    sdnn_settings : BioVariableGraphSettings = field(default_factory=BioVariableGraphSettings)
    poi_rat_settings : BioVariableGraphSettings = field(default_factory=BioVariableGraphSettings)