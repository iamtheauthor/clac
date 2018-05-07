from collections import namedtuple
import configparser
import os
from typing import Union, Any

from . import BaseConfigLayer  # , NoConfigKey

_SplitKey = namedtuple('SplitKey', 'section options')


class IniLayer(BaseConfigLayer):
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
