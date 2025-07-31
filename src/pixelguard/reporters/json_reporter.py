import json

from .base import BaseReporter


class JSONReporter(BaseReporter):

    def __init__(self, output_path: str):
        self.output_path = output_path

    def report_single(self, analysis):
        with open(self.output_path, "w") as file:
            json.dump(self._serialize_analysis(analysis), file, indent=2)

    def _serialize_analysis(self, analysis):
        return analysis.__dict__

    def report_batch(self, report):
        with open(self.output_path, "w") as file:
            json.dump(
                [self._serialize_analysis(analysis) for analysis in report.analyses],
                file,
                indent=2,
            )
