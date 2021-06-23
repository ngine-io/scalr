from scalr.log import log


class Factory:

    def __init__(self):
        self.cloud_classes = dict()

    def parse(self, config: dict):
        raise NotImplementedError()

    def get_instance(self, name: str, config: dict) -> object:
        try:
            log.info(f"Parsed config for {name}")

            obj_class = self.cloud_classes[name]
            obj = obj_class()
            obj.configure(self.parse(config=config))
            return obj
        except KeyError as e:
            raise NotImplementedError(f"{e} not implemented")
