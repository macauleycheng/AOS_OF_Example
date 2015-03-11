#!/usr/bin/python

import os

cwd=os.getcwd()
os.unsetenv('PYTHONPAHT')
os.environ['PYTHONPATH']=cwd
os.putenv('PYTHONPATH', cwd)


