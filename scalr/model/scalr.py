from pydantic import BaseModel


class Scalr(BaseModel):
    kind: str
    min: int = 0
    max: int = 0
    name: str = "scalr"
    launch_config: dict = dict()
    dry_run: bool = False
    max_step_down: int = 1
    scale_down_selection: str = "random"
    cooldown: int = 300
