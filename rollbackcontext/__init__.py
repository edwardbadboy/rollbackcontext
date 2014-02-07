# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#

import sys
from collections import deque, namedtuple


class RollbackContext(object):
    '''
    A context manager for recording and playing rollback.
    The first exception will be remembered and re-raised after rollback

    Sample usage:
    with RollbackContext() as rollback:
        step1()
        rollback.push(lambda: undo step1)
        def undoStep2(arg): pass
        step2()
        rollback.push(undoStep2, someArg)

    When rollback exits, it runs the undo functions in reverse order.
    Firstly it runs undoStep2(), then the lambda to undo step1.

    More examples see tests/test_rollbackcontext.py .
    '''

    class Undo(namedtuple('Undo', ['undo', 'autoCommit', 'args', 'kwargs'])):
        def setAutoCommit(self):
            self.autoCommit[0] = True

    def __init__(self, *args):
        self._finally = deque()
        self._lastUndo = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        According to Python official doc. This function should only re-raise
        the exception from undo functions. Python automatically re-raises the
        original exception when this function does not return True.
        http://docs.python.org/2/library/stdtypes.html#contextmanager.__exit__
        """
        undoExcInfo = None
        for func, autoCommit, args, kwargs in self._finally:
            if (exc_type is None) and autoCommit[0]:
                # The "with" statement exits without exception,
                # so skip the auto-committing undos.
                continue

            try:
                func(*args, **kwargs)
            except Exception:
                # keep the earliest exception info
                if undoExcInfo is None:
                    undoExcInfo = sys.exc_info()

        if exc_type is None and undoExcInfo is not None:
            raise undoExcInfo[0], undoExcInfo[1], undoExcInfo[2]

    def _push(self, func, toTop, args, kwargs):
        undo = self.Undo(func, [False], args, kwargs)
        if toTop:
            self._finally.appendleft(undo)
        else:
            self._finally.append(undo)
        return undo

    def push(self, func, *args, **kwargs):
        return self._push(func, True, args, kwargs)

    def pushBottom(self, func, *args, **kwargs):
        return self._push(func, False, args, kwargs)

    def commitAll(self):
        self._finally.clear()
