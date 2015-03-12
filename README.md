# AOS_OF_Example
Test Case for AOS Hybrid Mode Openflow

Code Originally from https://github.com/Broadcom-Switch/of-dpa.

We modified the file architecture and use real word case as an exmple for APP develop reference.

It all writed by statically configuration.

Each folder means a case, each file means a flow or a grouop.

I hope from file name, you can known what it is done.

"working_set.json" on each folder, it is used to execuse all flow and group json file.

"StartScript.py" on each folder, it is a start python file. Run this file will start the case.

Usage example: (on AOS_OF_Example folder)

ryu-manager 01-ping-each-other/01-2ClientInSameVLAN/StartScript.py

NOTE: If it can't find ofdpa module, please set the PYTHONPATH to the AOS_OF_Example
      or "source set_python_path.sh"
