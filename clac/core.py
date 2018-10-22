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

"""Default configuration Plugin for the pedestal framework."""
from abc import ABCMeta, abstractmethod
from collections.abc import Mapping
import enum
import os
from typing import Any, Type, Set, Tuple, Optional, Iterator, Dict

from .exceptions import NoConfigKey, MissingLayer, ImmutableLayer


class DictStructure(enum.Enum):
    Split = enum.auto()
    Flat = enum.auto()


class BaseConfigLayer(Mapping, metaclass=ABCMeta):
    """Abstract Base class for ConfigLayer Implementation

    This class cannot be used directly, and will raise ``TypeError`` if
    instantiated.  Rather, it is meant to be subclassed to perform its own
    application-specific configuration handling.  For example, a subclass named
    ``ConfLayer`` might be created to read UNIX-style configuration files.

    .. important:: Because this class is based off of the stdlib abc.Mapping
        abstract class, there are abstract methods not defined in this class
        which must still be defined by subclasses

    :param name: The qualified name of the config layer instance.  Will be
        used to look up the specified layer by the CLAC.  This name should
        not be changed after instantiation.
    """
    def __init__(self, name: str, mutable: bool = False) -> None:
        self._layer_name: str = name
        self._mutable = mutable
        if not self.mutable:
            # Remove the functions that are not needed
            del self.setdefault
            del self.__setitem__

    def get(self, key: str, default=None) -> Any:
        """Gets the value for the specified ``key``

        Returns ``default`` if ``key`` is not found.
        """
        # ! We must override this method, since we need to cover LookupError
        # ! specifically, rather than KeyError.

        try:
            return self[key]
        except LookupError:
            return default

    def setdefault(self, key: str, default: Any = None) -> Any:
        self.assert_mutable()
        try:
            return self[key]
        except LookupError:
            self[key] = default
            return default

    def __setitem__(self, key: str, value: Any) -> None:
        self.assert_mutable()
        raise NotImplementedError(f"__setitem__ is not implemented for class: {self.__class__.__name__}")

    def assert_mutable(self):
        if not self.mutable:
            raise ImmutableLayer(f"Attempted modification of immutable layer: {self._layer_name}")

    @property
    def mutable(self):
        return self._mutable

    @property
    def name(self):
        return self._layer_name

    @property
    @abstractmethod
    def names(self):
        """Returns the full list of keys in the Layer"""
        pass


_GET = object


class DictLayer(BaseConfigLayer):
    """A config layer based on ``dict``."""
    def __init__(
            self,
            name: str,
            config_dict: Optional[dict] = None,
            mutable: bool = False,
            dot_strategy: DictStructure = DictStructure.Flat
    ) -> None:

        super().__init__(name, mutable)
        if not config_dict:
            config_dict = {}
        self._config_dict = dict(config_dict)

        # ! Need implemetation plan for dot-structure methods
        if dot_strategy not in DictStructure:
            memb = f'{DictStructure.__module__}.{DictStructure.__name__}'
            msg = f'dot_strategy param must be a member of the {memb} enum.'
            raise ValueError(msg)
        self.dot_strategy = dot_strategy

    def __getitem__(self, key: str) -> Any:
        """Returns the value stored by ``key``

        This interface is strategy-aware, and will search the dict according
        to the strategy.
        """
        if self.dot_strategy is DictStructure.Split:
            return self.__dot_split_operation(key)
        if self.dot_strategy is DictStructure.Flat:
            return self._config_dict[key]
        raise ValueError('dot_strategy is not a known type')

    def __setitem__(self, key: str, value: Any) -> None:
        if self.dot_strategy is DictStructure.Split:
            self.__dot_split_operation(key, value)
            return None
        if self.dot_strategy is DictStructure.Flat:
            self._config_dict[key] = value
            return None
        raise ValueError('dot_strategy is not a known type')

    def __dot_split_operation(self, key_str: str, value=_GET) -> Any:
        *keylist, last_key_part = key_str.split('.')

        current_val = self._config_dict
        for keypart in keylist:
            try:
                current_val = current_val[keypart]
            except LookupError:
                raise NoConfigKey(key_str) from None

        if value is _GET:
            current_val = current_val[last_key_part]
            return current_val
        current_val[last_key_part] = value
        return None

    def __iter__(self) -> Iterator[str]:
        """Returns an iterator over :meth:`names`"""
        return iter(self.names)

    def __len__(self) -> int:
        """Returns the length of the :meth:`names`"""
        return len(self.names)

    def __dot_split_keys(self):
        def has_subkey(value):
            return hasattr(value, 'keys')

        def get_subkeys(dct, context=''):
            keyset = set()
            for key in dct:
                full_name = f'{context}.{key}' if context else key
                val = dct[key]
                if not has_subkey(val):
                    keyset.add(full_name)
                    continue
                keyset |= get_subkeys(val, full_name)
            return keyset

        return get_subkeys(self._config_dict)

    @property
    def names(self) -> Set[str]:
        """Returns a strategy-aware set of valid keys"""
        if self.dot_strategy is DictStructure.Split:
            return self.__dot_split_keys()
        if self.dot_strategy is DictStructure.Flat:
            return set(self._config_dict.keys())
        raise ValueError('dot_strategy is not a known type')


# pylint: disable=R0901
class EnvLayer(DictLayer):
    def __init__(self, name, sep='_'):
        super().__init__(name, os.environ, False)
        self._separator = sep

    def __getitem__(self, key):
        transkey = key.replace('_', '.')
        return super()[transkey]  # pylint: disable=E1136


class CLAC:
    """Clac Layerizes Application Configuraton.

    :meth:`__init__` parameters are the same as :meth:`add_layers`.
    """
    def __init__(self, *layers: BaseConfigLayer) -> None:
        self._lookup: Dict[str, BaseConfigLayer] = dict()
        self.add_layers(*layers)

    def __getitem__(self, key: str) -> Any:
        if not key:
            raise ValueError('key param must be non-empty string.')

        for layer in self._lookup.values():
            try:
                rv = layer[key]
                break
            except LookupError:
                pass
        else:
            raise NoConfigKey(key)
        return rv

    def get(self,
            key: str,
            default: Any = None,
            layer_name: str = None,
            callback: Type = None
            ) -> Any:
        """Gets values from config layers according to ``key``.

        Returns ``default`` if value is not found or LookupError is raised.

        If ``layer_name`` is specified, the method will perform all of the same
        actions, but only against the layer with the specified name.  Must be
        a str or None.  Defaults to None.

        If ``callback`` is specified, the method will pass the retrieved value
        to the callback, and return the result.  If ``callback`` is None, the
        original result is returned as-is.

        .. warning:: If the value is not found, ``callback`` will not be
           executed on the default value.  Applications should provide
           complete and prepared default values to the method.

        :raises MissingLayer: if ``layer_name`` is specified but no layer
            with that name has been added.
        :return: The value retrieved from the config layers, or ``default``
            if no entry was found.

        .. note:: If an exception is desired instead of a default value,
            ``__getitem__`` syntax (``clac_instance[key]``) should be used
            instead.  This will raise a ``NoConfigKey`` exception.  However,
            the ``__getitem__`` syntax does not support additional arguments.
            This means that only :meth:`get` will support defaults and
            coercion, and only ``__getitem__`` will support exception
            bubbling.
        """
        if layer_name and layer_name not in self._lookup:
            raise MissingLayer(layer_name)

        obj = self._get_layer(layer_name) if layer_name else self

        try:
            rv = obj[key]  # type: ignore
        except LookupError:
            return default
        if callback:
            rv = callback(rv)
        return rv

    def __setitem__(self, key: str, value) -> None:
        # Simpler than the getitem implemetation:
        # Find the first mutable layer, and then mutate it.
        for layer in self._lookup.values():
            if layer.mutable:
                layer[key] = value
                return None
        raise ImmutableLayer("No mutable layers detected")

    def setdefault(self, key: str, default: Any = None) -> Any:
        for layer in self._lookup.values():
            if layer.mutable:
                return layer.setdefault(key, default)

    def _get_layer(self, name: str) -> BaseConfigLayer:
        """Helper function to retrieve layers directly."""
        try:
            return self._lookup[name]
        except KeyError:
            raise MissingLayer(name) from None

    def add_layers(self, *layers: BaseConfigLayer):
        """Adds layers to the lookup set.  Called by :meth:`__init__`

        :param layers: A FIFO list of ConfigLayer instances.
            The first layer in this list will be the first layer queried.
        """
        for layer in layers:
            self._lookup[layer.name] = layer

    def remove_layer(self, name: str, error_ok: bool = True):
        """Remove layer ``name`` from the manager.

        :param name: The name of the layer to be removed.
        :param error_ok: bool specificying whether to ignore errors. Defaults
            to True. Will check to make sure layer is missing.
        :raises: :class:`MissingLayer` if name is not found in lookup and
            ``error_ok`` is False
        """
        try:
            del self._lookup[name]
        except KeyError:
            if not error_ok:
                raise MissingLayer(name) from None
            assert name not in self

    def __contains__(self, name: str):
        """True if ``name`` in layer name list"""
        return name in self._lookup

    @property
    def names(self) -> Set[str]:
        """Returns a set of all unique config keys from all layers."""
        nameset: Set = set()
        for layer in self._lookup.values():
            nameset.update(layer.names)
        return nameset

    def resolve(self, key: str) -> Tuple[str, Any]:  # noqa
        """Returns that name of the layer accessed, and the value retrieved.

        :param key: The key to search for.
        :raises NoConfigKey: ``key`` not in any layer.
        :return: 2-tuple: (layer, value)
        """

        for layer in self._lookup:
            try:
                rv = self.get(key, layer_name=layer)
            except NoConfigKey:
                continue
            else:
                return layer, rv
        raise NoConfigKey(key)

    def build_lri(self, key_first=False) -> Set[Tuple[str, Any]]:
        """Returns the Layer Resolution Index (LRI)

        The LRI is a ``set`` of 2-tuples which contain the first layer that a
        key can be found in, and the key itself.

        If ``key_first`` is True, the tuples will be structured as
        ``(key, name)``.  Default is False: ``(name, key)``
        """
        pairs = [(l.name, set(l.names)) for l in self._lookup.values()]
        name_index: Set[str] = set()
        lri = set()

        def rvsd(tup: Tuple[str, str]) -> Tuple[str, str]:
            if key_first:
                tup = (tup[1], tup[0])
            return tup

        while pairs:
            layername, layerset = pairs.pop(0)
            layerset -= name_index
            lri.update([
                rvsd((layername, key))
                for key in layerset
            ])
            name_index |= layerset
        return lri
