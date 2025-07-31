from abc import ABC, abstractmethod


class BaseReporter(ABC):
    @abstractmethod
    def report_single(self, analysis):
        pass

    @abstractmethod
    def report_batch(self, report):
        pass
