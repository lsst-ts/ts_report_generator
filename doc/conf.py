"""Sphinx configuration file for an LSST stack package.

This configuration only affects single-package Sphinx documentation builds.
For more information, see:
https://developer.lsst.io/stack/building-single-package-docs.html
"""

from documenteer.conf.pipelinespkg import *

project = "ts_report_generator"
html_theme_options["logotext"] = project  # type: ignore # noqa
html_title = project
html_short_title = project

# Support the sphinx extension of plantuml
extensions.append("sphinxcontrib.plantuml")  # type: ignore # noqa

# Put the path to plantuml.jar
plantuml = "java -jar /home/saluser/plantuml.jar"
