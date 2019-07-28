#!/usr/bin/python3

from yarn.frontend.console import run_in_console
from yarn import YarnController
import sys

if __name__=="__main__":
    controller=YarnController(sys.argv[1], "console", False)
    run_in_console(controller)
