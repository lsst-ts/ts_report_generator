.. py:currentmodule:: lsst.ts.report.generator

.. _lsst.ts.report.generator:

########################
lsst.ts.report.generator
########################

.. Paragraph that describes what this Python module does and links to related modules and frameworks.

Report generator is designed to produce reports from activities recorded in the EFD.

An "activity" is composed of a single "Actor" and any number of "Participants", both are components in the control system communicating over the observatory control system middleware (e.g. CSCs, SAL Scripts, etc.).
That means, the interaction between Actor and Participants are all stored in the EFD, which is the data source used by report generator to produce reports.

.. _lsst.ts.report.generator-using:

Using lsst.ts.report.generator
==============================

Command line
------------

Currently, report generator provides a command line executable that produces UML sequence diagrams of activities.

There are a variety of command line arguments that can control which information is included in these diagrams.

You can see all the available options by running 

.. prompt:: bash

   generate_report -h

At a minimum, an activity is defined by a start and end timestamp, and Actor and at least one Participant.
For example:

.. prompt:: bash

   generate_report --efd-name tucson_teststand_efd \
                --time_start 2022-09-13T00:00:00 \
                --time_end 2022-09-15T00:00:00 \
                --actor Script:200084 \
                --participants ATAOS

It is also possible to provide an event from the actor that tracks the start/end of the operation in that same time window.

.. prompt:: bash

   generate_report --efd-name tucson_teststand_efd \
      --time_start 2022-09-13T00:00:00 \
      --time_end 2022-09-15T00:00:00 \
      --actor Script:200084 \
      --a-event logevent_state \
      --participants ATAOS

If the first mode, the diagram is generated for the entire time window.
In the second mode, it will use the time from the first and last event sample in that time window.

If an actor event is provided, the name of the event appears in the activity diagram.
It is possible to provide an event attribute to be displayed as well:

.. prompt:: bash

   generate_report --efd-name tucson_teststand_efd \
      --time_start 2022-09-13T00:00:00 \
      --time_end 2022-09-15T00:00:00 \
      --actor Script:200084 \
      --a-event logevent_state \
      --actor-event-attribute state \
      --participants ATAOS

And since some of these event attributes are enumerations, it is possible to provide the name of the enumeration and the import path:

.. prompt:: bash

   generate_report --efd-name tucson_teststand_efd \
      --time_start 2022-09-13T00:00:00 \
      --time_end 2022-09-15T00:00:00 \
      --actor Script:200084 \
      --a-event logevent_state \
      --actor-event-attribute state \
      --a-event-enum ScriptState \
      --actor-event-enum-import-path lsst.ts.idl.enums.Script \
      --participants ATAOS

In this basic mode of operation it will generate a report with the commands sent from the actor to the participants and the acknowledgements received.

Furthermore, it is also possible to provide a list of event names from the participants to include in the activity diagram.

.. prompt:: bash

   generate_report --efd-name tucson_teststand_efd \
      --time_start 2022-09-13T00:00:00 \
      --time_end 2022-09-15T00:00:00 \
      --actor Script:200084 \
      --a-event logevent_state \
      --actor-event-attribute state \
      --a-event-enum ScriptState \
      --actor-event-enum-import-path lsst.ts.idl.enums.Script \
      --participants ATAOS \
      --participants-events logevent_summaryState,logevent_configurationApplied

Note we provided 2 events from the participant, separated by a comma.
In this mode the name of the event is used to indicate the event was published. As with the actor we can specify an event attribute to display alongside the name:

.. prompt:: bash

   generate_report --efd-name tucson_teststand_efd \
      --time_start 2022-09-13T00:00:00 \
      --time_end 2022-09-15T00:00:00 \
      --actor Script:200084 \
      --a-event logevent_state \
      --actor-event-attribute state \
      --a-event-enum ScriptState \
      --actor-event-enum-import-path lsst.ts.idl.enums.Script \
      --participants ATAOS \
      --participants-events logevent_summaryState,logevent_configurationApplied \
      --participants-events-attributes summaryState:configurations,version

Note that we use a colon to separate attributes from different events and comma to separate attributes from the individual events.
It is also possible to add enumerations to translate the value of an event.

.. prompt:: bash

   generate_report --efd-name tucson_teststand_efd \
      --time_start 2022-09-13T00:00:00 \
      --time_end 2022-09-15T00:00:00 \
      --actor Script:200084 \
      --a-event logevent_state \
      --actor-event-attribute state \
      --a-event-enum ScriptState \
      --actor-event-enum-import-path lsst.ts.idl.enums.Script \
      --participants ATAOS \
      --participants-events logevent_summaryState,logevent_configurationApplied \
      --participants-events-attributes summaryState:configurations,version \
      --participants-events-attributes-enum State: \
      --participants-events-enum-import-path lsst.ts.salobj:

Providing the enumeration follow the same format as that of the attributes, comma separates values for each attribute and colon separate values from events.

By default the report is written to the terminal.
Users can redirect the report to a file by adding the ``-o output.uml`` to the command line arguments.
The output is in text format and can be converted to a png using tools like plantuml.

Running the command above generates the following sequence diagram:

.. uml:: example-sequence.uml
    :caption: Activity sequence diagram for the output of the example above.


.. toctree linking to topics related to using the module's APIs.

.. .. toctree::
..    :maxdepth: 1

.. _lsst.ts.report.generator-contributing:

Contributing
============

``lsst.ts.report.generator`` is developed at https://github.com/lsst-ts/ts_report_generator.
You can find Jira issues for this module under the `ts_report_generator <https://jira.lsstcorp.org/issues/?jql=project%20%3D%20DM%20AND%20component%20%3D%20ts_report_generator>`_ component.

.. If there are topics related to developing this module (rather than using it), link to this from a toctree placed here.

.. .. toctree::
..    :maxdepth: 1

.. .. _lsst.ts.report.generator-scripts:

.. Script reference
.. ================

.. .. TODO: Add an item to this toctree for each script reference topic in the scripts subdirectory.

.. .. toctree::
..    :maxdepth: 1

.. _Version_History:

Version History
===============

.. toctree::
    version-history
    :maxdepth: 1

.. .. _lsst.ts.report.generator-pyapi:

Python API reference
====================

.. automodapi:: lsst.ts.report.generator
   :no-main-docstr:
   :no-inheritance-diagram:
