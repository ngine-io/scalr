from pydantic import BaseModel


class Scalr(BaseModel):
    min: int = 0
    max: int = 0
    name: str = "scalr"
    dry_run: bool = False
    max_step_down: int = 1
    scale_down_selection: str = "random"
    cooldown: int = 300
    launch_config: dict = dict()
