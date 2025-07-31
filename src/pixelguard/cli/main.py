import click

from src.pixelguard.cli.commands import (
    analyze_single_image,
    analyze_batch,
    show_config,
    show_env_vars,
)


@click.group()
def app():
    pass


app.add_command(analyze_single_image)
app.add_command(analyze_batch)
app.add_command(show_config)
app.add_command(show_env_vars)
