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

import unittest

from rollbackcontext import RollbackContext


class FirstError(Exception):
    '''A hypothetical exception to be raise in the test firstly.'''
    pass


class SecondError(Exception):
    '''A hypothetical exception to be raise in the test secondly.'''
    pass


class RollbackContextTests(unittest.TestCase):

    def setUp(self):
        self._r = []

    def _append(self, value=None):
        self._r.append(value)

    def _raise(self, exception=FirstError):
        raise exception()

    def test_rollback(self):
        with RollbackContext() as rollback:
            rollback.push(self._append, 1)
            rollback.push(self._append, 0)
        self.assertEquals(self._r, [0, 1])

    def test_rollback_bottom(self):
        with RollbackContext() as rollback:
            rollback.pushBottom(self._append, 1)
            rollback.push(self._append, 0)
            rollback.pushBottom(self._append, 2)
        self.assertEquals(self._r, [0, 1, 2])

    def test_raise(self):
        try:
            with RollbackContext() as rollback:
                rollback.push(self._append, 2)
                rollback.push(self._append, 1)
                raise FirstError()
                rollback.push(self._append, 0)
        except FirstError:
            # All undo before the FirstError should be run
            self.assertEquals(self._r, [1, 2])
        else:
            self.fail('Should have raised FirstError')

    def test_raise_undo(self):
        try:
            with RollbackContext() as rollback:
                rollback.push(self._append, 1)
                rollback.push(self._raise)
                rollback.push(self._append, 0)
        except FirstError:
            # All undo should be run
            self.assertEquals(self._r, [0, 1])
        else:
            self.fail('Should have raised FirstError')

    def test_raise_prefer_original(self):
        try:
            with RollbackContext() as rollback:
                rollback.push(self._raise, SecondError)
                raise FirstError()
        except FirstError:
            pass
        except SecondError:
            self.fail('Should have preferred FirstError to SecondError')
        else:
            self.fail('Should have raised FirstError')

    def test_raise_prefer_first_undo(self):
        try:
            with RollbackContext() as rollback:
                rollback.push(self._raise, SecondError)
                rollback.push(self._raise, FirstError)
        except FirstError:
            pass
        except SecondError:
            self.fail('Should have preferred FirstError to SecondError')
        else:
            self.fail('Should have raised FirstError')

    def test_autocommit(self):
        with RollbackContext() as rollback:
            rollback.push(self._append, 2)
            rollback.push(self._append, 1).setAutoCommit()
            rollback.push(self._append, 0)
        self.assertEquals(self._r, [0, 2])

    def test_raise_no_commit(self):
        try:
            with RollbackContext() as rollback:
                rollback.push(self._append, 2)
                rollback.push(self._append, 1).setAutoCommit()
                rollback.push(self._append, 0)
                raise FirstError()
        except FirstError:
            # Exception is from the "with",
            # so all the undos before the FirstError should be run.
            self.assertEquals(self._r, [0, 1, 2])
        else:
            self.fail('Should have raised FirstError')

    def test_raise_undo_autocommit(self):
        try:
            with RollbackContext() as rollback:
                rollback.push(self._append, 2)
                rollback.push(self._append, 1).setAutoCommit()
                rollback.push(self._append, 0)
                rollback.push(self._raise, FirstError)
        except FirstError:
            # Exception is from the undos, the with itself is successfull,
            # so all the undos before the FirstError should be run except
            # auto-committing undos.
            self.assertEquals(self._r, [0, 2])
        else:
            self.fail('Should have raised FirstError')

    def test_commitAll(self):
        with RollbackContext() as rollback:
            rollback.push(self._append, 2)
            rollback.push(self._append, 1)
            rollback.push(self._append, 0)
            rollback.commitAll()
        self.assertEquals(self._r, [])
