from scalr.log import log


class Factory:

    def __init__(self, config: dict = dict()):
        self.config = config
        self.cloud_classes = dict()

    def parse(self, data) -> dict:
        raise NotImplementedError()

    def get_instance(self, name: str) -> object:
        try:
            # Validate config
            Config = self.parse()
            log.info(f"Parsed config for policy {name}")

            obj_class = self.cloud_classes[name]
            obj = obj_class()
            obj.configure(Config)
            return obj
        except KeyError as e:
            msg = f"{e} not implemented"
            raise NotImplementedError(msg)
