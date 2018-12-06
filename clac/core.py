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
from typing import Any, Callable, Set, Tuple, Optional, Iterator, Dict

from .exceptions import NoConfigKey, MissingLayer, ImmutableLayer, LayerOverwriteError


class DictStructure(enum.Enum):
    """Enum for :class:`DictLayer` structuring strategy.

    This enum class exposes two variants:

    - ``Split``
    - ``Flat``

    See :class:`DictLayer` for more info.
    """
    Split = enum.auto()
    Flat = enum.auto()


class BaseConfigLayer(Mapping, metaclass=ABCMeta):
    """Abstract Base class for ConfigLayer Implementation

    This class cannot be used directly, and will raise ``TypeError`` if
    instantiated.  Rather, it is meant to be subclassed to perform its own
    application-specific configuration handling.  For example, a subclass named
    ``ConfLayer`` might be created to read UNIX-style configuration files.

    .. important:: Because this class is based off of the stdlib
        collections.abc.Mapping abstract class, there are abstract methods not
        defined in this class which must still be defined by subclasses.

    :param name: The qualified name of the config layer instance.  Will be
        used to look up the specified layer by the CLAC.  This name should
        not be changed after instantiation.
    :param mutable: ``bool`` representing whether the layer allows mutation.
        Readable using the :meth:`mutable` property.
    """
    def __init__(self, name: str, mutable: bool = False) -> None:
        self._layer_name: str = name
        self._mutable = mutable

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
        """If ``key`` is in the lookup, return its value.

        If ``key`` is not in the lookup, insert key with a value of
        ``default`` and return ``default``. ``default`` defaults to ``None``.
        """
        self.assert_mutable()
        try:
            return self[key]
        except LookupError:
            self[key] = default
            return default

    def __setitem__(self, key: str, value: Any) -> None:
        self.assert_mutable()  # pragma: no cover
        raise NotImplementedError(
            f"__setitem__ is not implemented for class: {self.__class__.__name__}"
        )

    def assert_mutable(self):
        """Raises :class:`ImmutableLayer` if layer is not mutable."""
        if not self.mutable:
            raise ImmutableLayer(
                f"Attempted modification of immutable layer: {self._layer_name}"
            )

    @property
    def mutable(self):
        """Whether the layer instance is mutable or not.

        This value is checked before all internal ``set``-style calls.  Any
        method which overrides :meth:`__setitem__` or :meth:`setdefault` must
        manually perform the check by calling :meth:`self.assert_mutable` with
        no arguments.
        """
        return self._mutable

    @property
    def name(self):
        """The name of the layer.

        The :class:`CLAC` instance will use this name as a lookup key for all
        layer-specific operations.  This will have no effect on non-specific
        ``get`` and ``set`` -type calls.
        """
        return self._layer_name

    @property
    @abstractmethod
    def names(self):
        """Returns the full list of keys in the Layer"""


_GET = object()


class DictLayer(BaseConfigLayer):
    """A config layer based on the python ``dict`` type.

    ``name``
        Behaves the same as all other layers.  See :class:`BaseConfigLayer`
        for more details.

    ``config_dict``
        An optional mapping object which contains the initial state of the
        configuration layer.  If non-truthy, ``mutable`` must be truthy.  If
        both are non-truthy, ``ValueError`` is raised.

        .. note:: Any truthy ``config_dict`` parameter will be passed to
            the ``dict()`` constructor.  This allows for a sequence of
            key-value pairs to be passed, but may interfere with other mapping
            types.

    ``mutable``
        A boolean representing whether the layer should allow mutation.  If
        non-truthy, ``config_dict`` must be truthy.  If both are non-truthy,
        ``ValueError`` is raised.

    ``dot_strategy``
        One of the variants of the :class:`DictStructure` enum. Defaults to
        :attr:`DictStructure.Flat`.

        :attr:`DictStructure.Split` will assume a nested dict structure.  Keys
            will be split by the ``.`` character.

        :attr:`DictStructure.Flat` will assume a flat dict structure. Keys are
            not modified before querying the underlying dict.

        This example illustrates both usages

        .. code-block:: python

           split = {
               'a': {
                   'b': {
                       'c': 'd'
                   }
               }
           }

           flat = {'a.b.c': 'd')

           layer1 = DictLayer('name', split, dot_strategy=DictStructure.Split)
           assert layer1['a.b.c'] == 'd'

           layer2 = DictLayer('name', flat, dot_strategy=DictStructure.Flat)
           assert layer2['a.b.c'] == 'd'
    """
    def __init__(
            self,
            name: str,
            config_dict: Optional[dict] = None,
            mutable: bool = False,
            dot_strategy: DictStructure = DictStructure.Flat
    ) -> None:

        super().__init__(name, mutable)
        if not config_dict:
            if not self.mutable:
                raise ValueError("config_dict cannot be empty for an immutable layer.")
            config_dict = {}
        assert isinstance(config_dict, (dict, Mapping))
        self._config_dict = config_dict

        if not isinstance(dot_strategy, DictStructure):
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
            try:
                return self._config_dict[key]
            except KeyError:
                raise NoConfigKey(key) from None
        raise ValueError('dot_strategy is not a known type')  # pragma: no cover

    def __setitem__(self, key: str, value: Any) -> None:
        self.assert_mutable()
        if self.dot_strategy is DictStructure.Split:
            self.__dot_split_operation(key, value)
            return None
        if self.dot_strategy is DictStructure.Flat:
            self._config_dict[key] = value
            return None
        raise ValueError('dot_strategy is not a known type')  # pragma: no cover

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
        raise ValueError('dot_strategy is not a known type')  # pragma: no cover


# pylint: disable=R0901
class EnvLayer(DictLayer):
    """A :class:`DictLayer` implemetation for reading environment variables."""
    def __init__(self, name, sep='_', prefix=None):
        super().__init__(name, os.environ, False)
        self._separator = sep
        self._prefix = prefix

    def __getitem__(self, key):
        if self._prefix:
            key = f'{self._prefix}.{key}'
        transkey = key.replace('.', self._separator).upper()
        return super().__getitem__(transkey)


class CLAC:
    """Configuration container/manager.

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
            callback: Callable = None
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
        """Call :meth:`BaseConfigLayer.set_default` on the first mutable layer."""
        for layer in self._lookup.values():
            if layer.mutable:
                return layer.setdefault(key, default)

        raise ImmutableLayer("No mutable layers detected")

    def _get_layer(self, name: str) -> BaseConfigLayer:
        """Helper function to retrieve layers directly."""
        try:
            return self._lookup[name]
        except KeyError:  # pragma: no cover
            raise MissingLayer(name) from None

    def add_layers(self, *layers: BaseConfigLayer):
        """Adds layers to the lookup set.  Called by :meth:`__init__`

        :param layers: A FIFO list of ConfigLayer instances.
            The first layer in this list will be the first layer queried.
        """
        for layer in layers:
            self._lookup[layer.name] = layer

    def insert_layers(self, *layers: BaseConfigLayer, raise_on_replace=True):
        """Inserts layers into the start of the lookup.

        If any layer name already exists, it will be inserted in the new
        position instead of retaining its old position.  This can be used to
        reorder the priority of any or all of the layers.  If a layer name is
        duplicated in the provided ``layers`` parameter, then the first value
        is taken, and the others are silently ignored.

        If any layer name conflicts are detected while moving old layers into
        the rebuilt lookup, the objects are compared for identity.  If the
        identities match, the new position of the layer is not overwritten with
        the layer's previous position.  If the identities do not match,
        :class:`LayerOverwriteError` is raised, and the operation is cancelled,
        having no effect on the original lookup.  This check is ignored if
        ``raise_on_replace`` is False (default is True).

        .. warning:: This function will rebuild the internal lookup, which can
           be expensive if there are a large number of entries.  However,
           having a large number of configuration sources is an unusual use
           case, and should not be considered a major performance impact which
           needs optimization.
        """

        new_lookup: Dict[str, BaseConfigLayer] = {}
        for new_layer in layers:
            new_lookup.setdefault(new_layer.name, new_layer)
        for old_layer in self._lookup.values():
            same = new_lookup.setdefault(old_layer.name, old_layer) is old_layer
            if raise_on_replace and not same:
                raise LayerOverwriteError(f'Layer would have been overwritten: {old_layer.name}')

        self._lookup = new_lookup

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

        # We have to make a failure object so we know that the get() call
        # did not find the object.
        _default = object()

        for layer in self._lookup:
            rv = self.get(key, _default, layer)
            if rv is _default:
                continue
            return layer, rv
        raise NoConfigKey(key)

    def build_lri(self) -> Set[Tuple[str, Any]]:
        """Returns the Layer Resolution Index (LRI)

        The LRI is a ``set`` of 2-tuples which contain the first layer that a
        key can be found in, and the key itself.

        If ``key_first`` is True, the tuples will be structured as
        ``(key, name)``.  Default is False: ``(name, key)``
        """
        pairs = [(l.name, set(l.names)) for l in self._lookup.values()]
        name_index: Set[str] = set()
        lri = set()

        while pairs:
            layername, layerset = pairs.pop(0)
            layerset -= name_index
            lri.update([(layername, key) for key in layerset])
            name_index |= layerset
        return lri

    @property
    def layers(self):
        """A copy of the internal layer lookup."""
        return self._lookup.copy()
