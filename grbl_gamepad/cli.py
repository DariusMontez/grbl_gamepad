# -*- coding: utf-8 -*-

"""Console script for grbl_gamepad."""
import sys
import click

from grbl_gamepad.jog_controller import main as jog

@click.command()
def main(args=None):
    """Console script for grbl_gamepad."""
    click.echo("Replace this message by putting your code into "
               "grbl_gamepad.cli.main")
    click.echo("See click documentation at http://click.pocoo.org/")

    jog()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
