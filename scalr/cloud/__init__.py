from scalr.log import log
from scalr.model.scalr import Scalr
import time
import math
import random
import uuid


class ScalrBase:

    def __init__(self):
        self.name: str = "scalr"
        self.min: int = 0
        self.max: int = 0
        self.launch_config: dict = dict()
        self.dry_run: bool = False
        self.max_step_down: int = 1
        self.scale_down_selection: str = "random"
        self.cooldown: int = 300

        self.desired: int = 0
        self.current: int = 0
        self.action: str = ""
        self.current_servers: list = None

    def configure(self, config: Scalr):
        self.name = config.name
        self.min = config.min
        self.max = config.max
        self.launch_config = config.launch_config
        self.dry_run = config.dry_run
        self.max_step_down = config.max_step_down
        self.scale_down_selection = config.scale_down_selection
        self.cooldown = config.cooldown

    def get_unique_name(self):
        uid = str(uuid.uuid4()).split('-')[0]
        return f"{self.name}-{uid}"

    def get_selected_server(self) -> str:
        if not self.current_servers:
            raise Exception("Error: no current servers found")
        if self.scale_down_selection == "oldest":
            index = 0
        else:
            index = random.randint(0, len(self.current_servers) - 1)
        return self.current_servers.pop(index)

    def get_current(self) -> list:
        raise NotImplementedError

    def ensure_running(self):
        raise NotADirectoryError

    def get_current_size(self) -> int:
        servers = self.get_current()
        if servers is None:
            raise Exception(f"Current servers is None")

        current = len(servers)
        log.info(f"current amount: {current}")
        return current

    def calc_diff(self, factor: float, current_size: int) -> int:
        log.info(f"factor: {factor}")
        if current_size <= 0:
            calc_current = 1
        else:
            calc_current = current_size

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

        diff = desired - current_size
        log.info(f"calculated diff: {diff}")

        if diff < 0 and 0 <= self.max_step_down < diff * -1:
            log.info(f"hit max down step: {self.max_step_down}")
            diff = self.max_step_down * -1
        return diff

    def scale(self, factor: float):
        if self.min > self.max:
            raise Exception(f"error: min {self.min} > max {self.max}")

        current_size = self.get_current_size()
        diff: int = self.calc_diff(factor=factor, current_size=current_size)

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
            log.info(f"needs cooldown: {self.cooldown}")
            for i in range(self.cooldown):
                print(f"cooling down: {i}\r", end='', flush=True)
                time.sleep(1)
            print("", flush=True)

    def scale_up(self, diff: int):
        raise NotImplementedError

    def scale_down(self, diff: int):
        raise NotImplementedError

    def __repr__() -> str:
        return f"{self.name}"
