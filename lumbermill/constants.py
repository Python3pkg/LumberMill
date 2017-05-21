# -*- coding: UTF-8 -*-
import os
import sys
import types
import logging
import socket
import platform


try:
    import zmq
    ZMQ_AVAILABLE = True
except ImportError:
    ZMQ_AVAILABLE = False

try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False

try:
    import __pypy__
    IS_PYPY = True
except ImportError:
    IS_PYPY = False

# In python3 the types constants have been eliminated.
if sys.hexversion > 0x03000000:
    TYPENAMES_TO_TYPE = {'None': type(None),
                         'Boolean': bool,
                         'Bool': bool,
                         'Integer': int,
                         'Int': int,
                         'Float': float,
                         'Str': str,
                         'String': str,
                         'Unicode': str,
                         'Tuple': tuple,
                         'List': list,
                         'Dictionary': dict,
                         'Dict': dict}
else:
    TYPENAMES_TO_TYPE = {'None': type(None),
                         'Boolean': bool,
                         'Bool': bool,
                         'Integer': int,
                         'Int': int,
                         'Float': float,
                         'Str': bytes,
                         'String': bytes,
                         'Unicode': str,
                         'Tuple': tuple,
                         'List': list,
                         'Dictionary': dict,
                         'Dict': dict}

# loglevel_string_to_loglevel_int
LOGLEVEL_STRING_TO_LOGLEVEL_INT = {'info': logging.INFO,
                                   'warn': logging.WARN,
                                   'error': logging.ERROR,
                                   'critical': logging.CRITICAL,
                                   'fatal': logging.FATAL,
                                   'debug': logging.DEBUG}

MY_HOSTNAME = socket.gethostname()
MY_SYSTEM_NAME = platform.system()
LUMBERMILL_BASEPATH = os.path.dirname(os.path.realpath(__file__))