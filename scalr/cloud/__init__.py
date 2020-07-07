from scalr.log import log
import time
import math


class ScalrBase:

    def __init__(self):
        self.current_servers: list = None
        self.min: int = 0
        self.max: int = 0
        self.name: str = "scalr"
        self.interval: int = 60
        self.policy: Policy
        self.launch_config: dict = dict()
        self.dry_run: bool = False
        self.max_step_down: int = 1
        self.desired: int = 0
        self.current: int = 0
        self.needs_cooldown: bool = False
        self.action: str = ""

    def get_current(self) -> list:
        raise NotImplementedError

    def ensure_running(self):
        raise NotADirectoryError

    def calc_diff(self, factor: float) -> int:

        log.info(f"factor: {factor}")
        if self.current <= 0:
            calc_current = 1
        else:
            calc_current = self.current

        desired = math.ceil(calc_current * factor)
        log.info(f"desired amount: {desired}")

        if self.max < desired:
            desired = self.max
            log.info(f"desired > max: reset to {desired}")

        elif self.min > desired:
            log.info(f"desired < min: reset to {desired}")
            desired = self.min

        log.info(f"desired {desired}")
        self.desired = desired

        diff = desired - self.current
        log.info(f"calculated diff: {diff}")

        if diff < 0 and self.max_step_down < diff * -1:
            log.info(f"hit max down step: {self.max_step_down}")
            diff = self.max_step_down * -1
        return diff

    def scale(self, factor: float):

        if self.min > self.max:
            raise Exception(f"error: min {self.min} > max {self.max}")

        servers = self.get_current()
        if servers is None:
            raise Exception(f"Current servers is None")

        self.current = len(servers)
        log.info(f"current amount: {self.current}")

        diff = calc_diff()

        if diff == 0:
            log.info(f"no action taken")
            self.action = "No action"
            self.ensure_running()
            return

        if diff > 0:
            self.scale_up(diff)
            self.action = f"Scaling up {diff}"

        elif diff < 0:
            diff = diff * -1
            self.scale_down(diff)
            self.action = f"Scaling down {diff}"

        self.ensure_running()

        if not self.dry_run:
            self.needs_cooldown = True
            log.info(f"needs cooldown")

    def scale_up(self, diff: int):
        raise NotImplementedError

    def scale_down(self, diff: int):
        raise NotImplementedError
