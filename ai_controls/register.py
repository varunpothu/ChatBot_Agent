from dataclasses import dataclass

@dataclass(frozen=True)
class Control:
    control_id: str
    area: str
    requirement: str
    evidence: str

CONTROLS = [
    Control("CTRL-01","Ownership","Each deployed model has an owner and escalation route.","model registry"),
    Control("CTRL-02","Data","Every source has provenance, version and effective dates.","document metadata"),
    Control("CTRL-03","Human oversight","Uncertain or policy-sensitive responses can be handed to a person.","review workflow"),
    Control("CTRL-04","Transparency","Responses expose supporting sources.","citation objects"),
    Control("CTRL-05","Change control","Model and prompt changes require evaluation evidence.","release checks"),
    Control("CTRL-06","Monitoring","Quality, safety and performance metrics are continuously measured.","runtime metrics"),
]

def control_register():
    return [c.__dict__ for c in CONTROLS]
