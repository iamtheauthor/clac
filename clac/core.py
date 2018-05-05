"""Default configuration Plugin for shall framework."""
from abc import ABCMeta, abstractproperty
from collections import OrderedDict, Mapping
from typing import Any, Type, Set, Tuple

from .exceptions import NoConfigKey, MissingLayer

RAISE = object()


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
        not be changed, and any behavior caused by changing it after
        instantiation is undefined.
    """
    def __init__(self, name: str) -> None:
        self._layer_name: str = name

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

    @property
    def name(self):
        return self._layer_name

    @property
    @abstractproperty
    def names(self):
        """Returns the full list of keys in the Layer"""
        er_msg = ' '.join([
            "names property has not been implemented for class:",
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

        :param coerce:  If not None, when get recieves a value, will cast
            to ``coerce``. Does not coerce ``default`` value if returned.
            Defaults to ``None``.
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

        assert self._get_mode() == 'FIFO'

        obj = self._get_layer(layer_name) if layer_name else self

        try:
            rv = obj[key]  # type: ignore
        except LookupError:
            return default
        if callback:
            rv = callback(rv)
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
