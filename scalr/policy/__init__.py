
from ..log import log


class PolicyBase:

    def __init__(self):
        super().__init__()
        self.target: int
        self.config: dict = dict()
        self.query: str

    def get_scaling_factor():
        raise NotImplementedError
