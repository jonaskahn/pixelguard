import csv

from .base import BaseReporter


class CSVReporter(BaseReporter):
    def __init__(self, output_path: str):
        self.output_path = output_path

    def report_single(self, analysis):
        with open(self.output_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["file_path", "is_problematic"])
            writer.writerow(
                [
                    getattr(analysis, "file_path", ""),
                    getattr(analysis, "is_problematic", ""),
                ]
            )

    def report_batch(self, report):
        with open(self.output_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["file_path", "is_problematic"])
            for analysis in report.analyses:
                writer.writerow(
                    [
                        getattr(analysis, "file_path", ""),
                        getattr(analysis, "is_problematic", ""),
                    ]
                )
