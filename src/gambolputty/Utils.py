# -*- coding: utf-8 -*-
import ast
import pprint
import random
import time
import os
import sys
import subprocess
import logging
import __builtin__
import signal
import Decorators

try:
    import __pypy__
    is_pypy = True
except ImportError:
    is_pypy = False

def reload():
    """
    Reload the whole GambolPutty process. This code is a direct copy from tornado-3.1.1-py2.7.egg/tornado/autoreload.py.
    """
    if hasattr(signal, "setitimer"):
        # Clear the alarm signal set by
        # ioloop.set_blocking_log_threshold so it doesn't fire
        # after the exec.
        signal.setitimer(signal.ITIMER_REAL, 0, 0)
    # sys.path fixes: see comments at top of file.  If sys.path[0] is an empty
    # string, we were (probably) invoked with -m and the effective path
    # is about to change on re-exec.  Add the current directory to $PYTHONPATH
    # to ensure that the new process sees the same path we did.
    path_prefix = '.' + os.pathsep
    if (sys.path[0] == '' and
            not os.environ.get("PYTHONPATH", "").startswith(path_prefix)):
        os.environ["PYTHONPATH"] = (path_prefix +
                                    os.environ.get("PYTHONPATH", ""))
    if sys.platform == 'win32':
        # os.execv is broken on Windows and can't properly parse command line
        # arguments and executable name if they contain whitespaces. subprocess
        # fixes that behavior.
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)
    else:
        try:
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except OSError:
            # Mac OS X versions prior to 10.6 do not support execv in
            # a process that contains multiple threads.  Instead of
            # re-executing in the current process, start a new one
            # and cause the current process to exit.  This isn't
            # ideal since the new process is detached from the parent
            # terminal and thus cannot easily be killed with ctrl-C,
            # but it's better than not being able to autoreload at
            # all.
            # Unfortunately the errno returned in this case does not
            # appear to be consistent, so we can't easily check for
            # this error specifically.
            os.spawnv(os.P_NOWAIT, sys.executable,
                      [sys.executable] + sys.argv)
            sys.exit(0)

def getDefaultEventDict(dict={}, caller_class_name=''):
    default_dict = KeyDotNotationDict({ "event_type": "Unknown",
                     "received_from": False,
                     "data": "",
                     "gambolputty": {
                        'event_id': "%032x" % random.getrandbits(128),
                        "source_module": caller_class_name
                     }
                    })
    default_dict.update(dict)
    return default_dict

def compileStringToConditionalObject(condition_as_string, mapping):
    """
    Parse a condition passed in as string.

    Example:

    lambda event:

    condition_as_string = "matched = VirtualHostName == 'www.gambolutty.com'", mapping = "event['%s']"

    condition_as_string = "lambda event: VirtualHostName == 'www.gambolutty.com'", mapping = "event['%s']"

     will be parsed and compiled to:
     matched = event['VirtualHostName'] == "www.gambolutty.com"
     matched = event.get('VirtualHostName', False) == "www.gambolutty.com"
    """
    try:
        # Build a complete expression from filter.
        transformer = AstTransformer(mapping)
        conditional_ast = ast.parse(condition_as_string)
        conditional_ast = transformer.visit(conditional_ast)
        conditional = compile(conditional_ast, '<string>', 'exec')
        return conditional
    except :
        etype, evalue, etb = sys.exc_info()
        logging.getLogger("compileStringToConditionalObject").error("%sCould not compile conditional %s. Exception: %s, Error: %s.%s" % (AnsiColors.WARNING, condition_as_string, etype, evalue, AnsiColors.ENDC))
        return False

class AstTransformer(ast.NodeTransformer):
    def __init__(self, mapping="%s"):
        ast.NodeTransformer.__init__(self)
        self.mapping = mapping

    def visit_Name(self, node):
        # ignore builtins and some other vars
        ignore_nodes = dir(__builtin__)
        ignore_nodes.extend(["matched", "dependency", "event"])
        if node.id in ignore_nodes:
            return node
        #pprint.pprint(self.mapping % node.id)
        #pprint.pprint(ast.dump(ast.parse(self.mapping % node.id)))
        new_node = ast.parse(self.mapping % node.id).body[0].value
        return new_node

class Buffer:
    def __init__(self, size, callback, interval=1):
        self.flush_size = size
        self.flush_interval = interval
        self.flush_callback = callback
        self.flush_timed_func = self.getTimedFlushMethod()
        self.flush_timed_func()
        self.buffer = []
        self.is_sending = False
        self.append = self.put

    def getTimedFlushMethod(self):
        @Decorators.setInterval(self.flush_interval)
        def timedFlush():
            if self.is_sending or len(self.buffer) == 0:
                return
            self.flush()
        return timedFlush

    def put(self, item):
        self.buffer.append(item)
        if len(self.buffer) == self.flush_size:
            self.flush()

    def flush(self):
        try:
            self.flush_callback(self.buffer)
            self.buffer = []
        finally:
            pass

    def bufsize(self):
        return len(self.buffer)

class BufferedQueue():
    def __init__(self, queue, buffersize=100, ):
        self.queue = queue
        self.buffersize = buffersize
        self.buffer = []
        self.is_sending = False
        self.flushBuffer()

    @Decorators.setInterval(1)
    def flushBuffer(self):
        if self.is_sending or len(self.buffer) == 0:
            return
        self.sendBuffer()

    def put(self, payload):
        # Wait till a running store is finished to avoid strange race conditions.
        while self.is_sending:
            time.sleep(.001)
        self.buffer.append(payload)
        if len(self.buffer) == self.buffersize:
            self.sendBuffer()

    def sendBuffer(self):
        self.is_sending = True
        self.queue.put(self.buffer)
        self.buffer = []
        self.is_sending = False

    def get(self, block=True, timeout=None):
        return self.queue.get(block, timeout)

    def qsize(self):
        return len(self.buffer) + self.queue.qsize()

    def __getattr__(self, name):
        return getattr(self.queue, name)

class KeyDotNotationDict(dict):
    def __init__(self, *args):
        dict.__init__(self, *args)

    def __getitem__(self, key):
        if "." not in key:
            return super(KeyDotNotationDict, self).__getitem__(key)
        tmp_data = super(KeyDotNotationDict, self)
        for current_key in key.split('.'):
            tmp_data = tmp_data.__getitem__(current_key)
        return tmp_data

    def __setitem__(self, key, value, dict=None):
        dict = dict if dict else super(KeyDotNotationDict, self)
        if "." not in key:
            return dict.__setitem__(key, value)
        current_key, remaining_keys = key.split('.', 1)
        dict = dict.__getitem__(current_key)
        self.__setitem__(remaining_keys, value, dict)

    def __delitem__(self, key):
        if "." not in key:
            return super(KeyDotNotationDict, self).__delitem__(key)
        tmp_data = super(KeyDotNotationDict, self)
        keys = key.split('.')
        idx_last = len(keys) - 1
        for idx, current_key in enumerate(keys):
            if idx != idx_last:
                tmp_data = tmp_data.__getitem__(current_key)
            else:
                tmp_data.__delitem__(current_key)

    def __contains__(self, key):
        if "." not in key:
            return super(KeyDotNotationDict, self).__contains__(key)
        try:
            tmp_data = super(KeyDotNotationDict, self)
            for current_key in key.split('.'):
                tmp_data = tmp_data.__getitem__(current_key)
            return True
        except KeyError:
            return False

    def get(self, key, default):
        if "." not in key:
            return super(KeyDotNotationDict, self).get(key, default)
        try:
            tmp_data = super(KeyDotNotationDict, self)
            for current_key in key.split('.'):
                tmp_data = tmp_data.__getitem__(current_key)
            return tmp_data
        except KeyError:
            return default

class AnsiColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    LIGHTBLUE = '\033[34m'
    YELLOW = '\033[33m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
