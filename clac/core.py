"""Default configuration Plugin for shall framework."""
from collections import OrderedDict
from typing import Any, AnyStr, Type, List, Tuple, Optional, Union

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

    def get(self, key: str) -> Any:
        """Gets the value for the specified ``key``"""
        er_msg = ("get() has not been implemented for class: ",
                  f"{self.__class__.__name__}")
        raise NotImplementedError(er_msg)

    @property
    def names(self):
        """Returns the full list of keys in the Layer"""
        er_msg = ("names property has not been implemented for class: ",
                  f"{self.__class__.__name__}")
        raise NotImplementedError(er_msg)

    def __contains__(self, key: str) -> bool:
        """Returns True if key exists in lookup, False otherwise"""
        er_msg = ("__contains__() has not been implemented for class: ",
                  f"{self.__class__.__name__}")
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

    def get(self,
            key: str,
            default: Any = _RAISE,
            layer_name: str = None,
            coerce: Type = None
            ) -> Any:
        """Gets values from config layers according to ``key``.

        :param key:         The name of the desired key.
        :param default:     The value to return if the key is not found. Leave
            blank to propogate :class:`NoConfigKey`
        :param layer_name:  The name of the layer to search.  If
            ``layer_name`` is not specified, all layers will be scanned in
            FIFO order. Defaults to ``None``.
        :param coerce:   If not None, when get recieves a value, will cast
            to ``coerce``. Does not coerce ``default`` value if returned.
            Defaults to ``None``.
        :raises: :class:`NoConfigKey` if the config key is not found and
            default is not specified.
        :raises: :class:`MissingLayer` if layer_name is specified but no layer
            with that name has been added.
        :return: The value retrieved from the config layers.
        """
        catch_exc = (NoConfigKey, KeyError)
        if layer_name:
            # * Search only one layer
            try:
                rv = self._get_layer(layer_name).get(key)
            except catch_exc:
                if default is _RAISE:
                    raise NoConfigKey(key) from None
                return default
            if coerce:
                rv = coerce(rv)
            return rv

        # * Search All layers

        # Should catch leaks from layer name being specified.
        assert not layer_name
        # Placeholder for later functionality.
        assert self._get_mode() == 'FIFO'

        for layer in self._lookup.values():
            try:
                rv = layer.get(key)
                break
            except catch_exc:
                pass
        else:
            if default is _RAISE:
                raise NoConfigKey(key) from None
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

    def remove_layer(self, name: AnyStr, error_ok: bool = True):
        """Remove layer ``name`` from the manager.

        :param name: The name of the layer to be removed.
        :param error_ok: bool specificying whether to ignore errors, defaults
            to True
        :raises: :class:`MissingLayer` if name is not found in lookup and
            ``error_ok`` is False
        """
        try:
            del self._lookup[name]
        except KeyError:
            if not error_ok:
                raise MissingLayer(name) from None

    def __contains__(self, name: str):
        return name in self._lookup

    @property
    def names(self):
        nameset = set()
        for layer in self._lookup.values():
            nameset.update(layer.names)
        return nameset

    def get_layer_resolution(self, key: Optional[str] = None) -> Union[Tuple[str, Any], List[Tuple[str, Any]]]:  # noqa
        if key is None:
            return self._build_lri()
        for layer in self._lookup:
            try:
                rv = self.get(key, layer_name=layer)
            except NoConfigKey:
                continue
            else:
                return (layer, rv)
        else:
            raise NoConfigKey(key)

    def _build_lri(self):
        pairs = [(l.name, set(l.names)) for l in self._lookup.values()]
        name_index = set()
        lri = set()

        while pairs:
            layername, layerset = pairs.pop(0)
            layerset -= name_index
            lri.update([(layername, key) for key in layerset])
            name_index |= layerset
        return lri
