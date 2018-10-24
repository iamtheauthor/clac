# Copyright 2018 Wesley Van Melle <van.melle.wes@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Batteries-included config layers for the clac library"""

from collections import namedtuple
import configparser
import os
from typing import Union, Any

from clac.core import BaseConfigLayer  # , NoConfigKey

_SplitKey = namedtuple('SplitKey', 'section options')


class IniLayer(BaseConfigLayer):
    """.ini file layer"""
    def __init__(
            self,
            name: str,
            *files: Union[str, os.PathLike]
    ) -> None:
        super().__init__(name)
        self._parser = configparser.ConfigParser()
        self._parser.read(files)

    def __getitem__(self, key: str) -> Any:
        sect, opt = self._split_key(key)
        rv = self._parser[sect][opt]
        return rv

    def __iter__(self):
        def itergen():
            for section in self._parser:
                for option in self._parser[section]:
                    yield self._unify_key(section, option)
        return itergen()

    @staticmethod
    def _unify_key(section: str, option: str) -> str:
        return '.'.join([section, option])

    @staticmethod
    def _split_key(key: str) -> _SplitKey:
        split_result = key.split('.', 1)
        spky = _SplitKey(*split_result)
        assert len(spky) == 2
        return spky

    def __len__(self):
        count = 0
        for section in self._parser:
            count += len(self._parser[section])
        return count

    @property
    def names(self):
        nameset = set()
        for sect in self._parser:
            for opt in self._parser[sect]:
                nameset.add(f'{sect}.{opt}')
        return nameset
