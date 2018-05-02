"""Default configuration Plugin for shall framework."""
from collections import OrderedDict
from typing import Any, Type, Set, Tuple

from .exceptions import NoConfigKey, MissingLayer

_RAISE = object()


class BaseConfigLayer:
    """Abstract Base class for ConfigLayer Implementation

    :param name: The qualified name of the config layer instance.  Will be
        used to look up the specified layer by the CLAC.  This name should
        not be changed, and any behavior caused by changing it after
        instantiation is undefined.
    """
    def __init__(self, name: str) -> None:
        self.name: str = name

    def get(self, key: str, default=_RAISE) -> Any:
        """Gets the value for the specified ``key``"""
        er_msg = ' '.join([
            "get() has not been implemented for class:",
            f"{self.__class__.__name__}"
        ])
        raise NotImplementedError(er_msg)

    @property
    def names(self):
        """Returns the full list of keys in the Layer"""
        er_msg = ' '.join([
            "names property has not been implemented for class:",
            f"{self.__class__.__name__}"
        ])
        raise NotImplementedError(er_msg)

    def __getitem__(self, key):
        """Returns the full list of keys in the Layer"""
        er_msg = ' '.join([
            "__getitem__() has not been implemented for class:",
            f"{self.__class__.__name__}"
        ])
        raise NotImplementedError(er_msg)

    def __contains__(self, x) -> bool:
        """Returns True if key exists in lookup, False otherwise"""
        er_msg = ' '.join([
            "__contains__() has not been implemented for class:",
            f"{self.__class__.__name__}"
        ])
        raise NotImplementedError(er_msg)


class CLAC:
    """Clac Layerizes Application Configuraton.

    :meth:`__init__` parameters are the same as :meth:`add_layers`.
    """
    def __init__(self, *layers: BaseConfigLayer) -> None:
        self._lookup: OrderedDict = OrderedDict()
        self.add_layers(*layers)

    def _get_mode(self) -> str:
        """Placeholder for later functionality"""
        return 'FIFO'

    def __getitem__(self, key: str) -> Any:
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
            coerce: Type = None
            ) -> Any:
        """Gets values from config layers according to ``key``.

        :param key:         The name of the desired key.
        :param default:     The uncoerced value to return if the key is not
            found. Defaults to None.
        :param layer_name:  The name of the layer to search.  If
            ``layer_name`` is not specified, all layers will be scanned in
            FIFO order. Defaults to ``None``.
        :param coerce:   If not None, when get recieves a value, will cast
            to ``coerce``. Does not coerce ``default`` value if returned.
            Defaults to ``None``.
        :raises: :class:`MissingLayer` if layer_name is specified but no layer
            with that name has been added.
        :return: The value retrieved from the config layers.
        """
        if layer_name:
            if layer_name not in self._lookup:
                raise MissingLayer(layer_name)
            try:
                rv = self._get_layer(layer_name).get(key)
            except LookupError:
                return default
            if coerce:
                rv = coerce(rv)
            return rv

        # * Search All layers
        # Should catch leaks from layer name being specified.
        assert not layer_name, 'layer_name was specified and not caught'
        # Placeholder for later functionality.
        assert self._get_mode() == 'FIFO'

        try:
            rv = self[key]
        except LookupError:
            return default
        if coerce:
            rv = coerce(rv)
        return rv

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
                return (layer, rv)
        else:
            raise NoConfigKey(key)

    def build_lri(self, reverse=False) -> Set[Tuple[str, Any]]:
        """Returns the Layer Resolution Index (LRI)

        The LRI is a ``set`` of 2-tuples (``name``, ``key``) which are the
        first layer that a key can be found, and the key itself, respectively.


        """
        pairs = [(l.name, set(l.names)) for l in self._lookup.values()]
        name_index: Set[str] = set()
        lri = set()

        def rvsd(tup: Tuple[str, str]) -> Tuple[str, str]:
            if reverse:
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
