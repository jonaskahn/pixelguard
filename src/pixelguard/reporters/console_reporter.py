from rich.console import Console

from .base import BaseReporter


class ConsoleReporter(BaseReporter):

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console()

    def report_single(self, analysis):
        self.console.print(
            f"[bold green]File:[/bold green] {getattr(analysis, 'file_path', '')}"
        )

        status = (
            "[bold red]PROBLEMATIC[/bold red]"
            if analysis.is_problematic
            else "[bold green]OK[/bold green]"
        )
        self.console.print(f"Status: {status}")

        if analysis.is_problematic and hasattr(analysis, "detection_results"):
            self.console.print("\n[bold yellow]Issues Found:[/bold yellow]")
            for result in analysis.detection_results:
                if result.is_problematic and result.issues:
                    for issue in result.issues:
                        self.console.print(f"  • {issue}")

        if self.verbose:
            self._display_detection_details(analysis)

    def _display_detection_details(self, analysis):
        if hasattr(analysis, "detection_results") and analysis.detection_results:
            self.console.print("\n[bold cyan]Detection Details:[/bold cyan]")
            for result in analysis.detection_results:
                status = (
                    "[red]FAILED[/red]"
                    if result.is_problematic
                    else "[green]PASSED[/green]"
                )
                self.console.print(
                    f"  {result.detector_name}: {status} (confidence: {result.confidence:.2f})"
                )

                if result.details:
                    for key, value in result.details.items():
                        if isinstance(value, dict):
                            self.console.print(f"    {key}:")
                            for sub_key, sub_value in value.items():
                                self.console.print(f"      {sub_key}: {sub_value}")
                        else:
                            self.console.print(f"    {key}: {value}")

    def report_batch(self, report):
        self.console.print(
            f"[bold blue]Batch Report:[/bold blue] {getattr(report.summary, 'problematic_images', 0)} problematic out of {getattr(report.summary, 'total_images', 0)} images."
        )
        if self.verbose:
            for analysis in getattr(report, "analyses", []):
                self._display_detection_details(analysis)
