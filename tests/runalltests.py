#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Run all test modules in current directory.
"""

import os, sys
import unittest
import doctest
import glob
import logging
from StringIO import StringIO

try:
    import fms
except ImportError:
    # runnning from source, not installed, add fms source path to system path
    fmspath = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
    sys.path.append(fmspath)

import fms
import fms.core
from fms.utils.parsers import YamlParamsParser

def sourceList():
    """
    Return list of all python modules except this one in current dir
    """
    liste = []
    for s in glob.glob("*.py"):
        if s == 'runalltests.py':
            continue
        s = s.split('.')[0]
        liste.append(s)
    return liste

def expList():
    """
    Return list of experiments conffiles in fixtures/experiments dir
    """
    return glob.glob("fixtures/experiments/*.yml")


old_dir = os.getcwd()
try:
    os.chdir(os.path.dirname(__file__))
except OSError:
    pass

logger = fms.core.set_logger('info','fms-tests')

logger.info("Running unittests")
suite = unittest.TestSuite()

for modtestname in sourceList():
    modtest = __import__(modtestname, globals(), locals(), [], -1)
    if hasattr(modtest, 'suite'):
        suite.addTest(modtest.suite())
    else:
        suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(modtest))

for root, dir, files in os.walk(os.path.dirname(fms.__file__)):
    for f in files:
        if os.path.splitext(f)[1] == '.py':
            head, tail = os.path.split(root)
            if tail == 'fms':
                suite.addTest(doctest.DocFileSuite(f, package='fms',
                    optionflags=+doctest.ELLIPSIS))
            else:
                if 'contrib' in head:
                    h, t = os.path.split(head)
                    if t == 'contrib':
                        suite.addTest(doctest.DocFileSuite(
                            os.path.join(os.path.split(root)[1], f),
                            package='fms.contrib',
                            optionflags=+doctest.ELLIPSIS))
                    else:
                        suite.addTest(doctest.DocFileSuite(
                            os.path.join(os.path.split(root)[1], f),
                            package='fms.contrib.%s' % t,
                            optionflags=+doctest.ELLIPSIS))
                else:
                    suite.addTest(doctest.DocFileSuite(
                        os.path.join(os.path.split(root)[1], f),
                        package='fms',
                        optionflags=+doctest.ELLIPSIS))

unittest.TextTestRunner(verbosity=2).run(suite)

for simconffile in expList():
    logger.info("Running %s" % simconffile)
    params = YamlParamsParser(simconffile)
    params['show_books'] = False
    params['timer'] = False
    params.outputfile = StringIO()
    (world, engineslist, agentslist) = fms.core.set_classes(params)
    for e in engineslist:
        e['instance'].run(world, agentslist, e['market']['instance'])
    benchfile = "%s.csv" % simconffile.split('.')[0]
    benchmark = open(benchfile).read()
    testresult = params.outputfile.getvalue()
    if not benchmark == testresult:
        logger.error("%s failed" % simconffile)
        print testresult
    else:
        logger.info("%s ok" % simconffile)
    params.close_files(1)
    agentslist[0].reset()

os.chdir(old_dir)

