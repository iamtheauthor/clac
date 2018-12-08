import pathlib
# import sys
from typing import Iterable

from pytest import raises, fixture, mark

# sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from clac import (
    CLAC, BaseConfigLayer, NoConfigKey, MissingLayer, ImmutableLayer, LayerOverwriteError
)

__here__ = pathlib.Path(__file__).resolve().parent


class SimpleLayer(BaseConfigLayer):
    def __init__(self, name, data, mutable=False):
        super().__init__(name, mutable)
        self.data = data

    def __setitem__(self, key, value):
        self.assert_mutable()
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, key) -> bool:
        return key in self.data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    @property
    def names(self) -> Iterable[str]:
        return self.data.keys()


@fixture(name='clac_layers')
def fixture_clac_layers():
    alpha_dict = {
        'test_key': 'test_value_alpha',
        'alpha_secret': 'abcde',
        'unique': '0123456789'
    }
    beta_dict = {
        'test_key': 'test_value_beta',
        'beta_secret': 'fghij',
    }
    gamma_dict = {
        'test_key': 'test_value_gamma',
        'beta_secret': 'klmno',
        'gamma_secret': 'gamma rules!',
    }
    alpha = SimpleLayer('alpha', alpha_dict)
    beta = SimpleLayer('beta', beta_dict)
    gamma = SimpleLayer('gamma', gamma_dict)

    yield alpha, beta, gamma


@fixture(name='mutable_layers')
def fixture_mutable_layers():
    alpha_dict = {
        'test_key': 'test_value_alpha',
        'alpha_secret': 'abcde',
        'unique': '0123456789'
    }
    beta_dict = {
        'test_key': 'test_value_beta',
        'beta_secret': 'fghij',
    }
    gamma_dict = {
        'test_key': 'test_value_gamma',
        'beta_secret': 'klmno',
        'gamma_secret': 'gamma rules!',
    }
    alpha = SimpleLayer('alpha', alpha_dict)
    beta = SimpleLayer('beta', beta_dict, mutable=True)
    gamma = SimpleLayer('gamma', gamma_dict)

    yield alpha, beta, gamma


def test_get_from_one_layer(clac_layers):
    alpha = clac_layers[0]
    simple_clac = CLAC(alpha)

    assert 'alpha' in simple_clac
    assert 'test_key' in simple_clac.names
    result1 = simple_clac['test_key']
    result2 = simple_clac.get('test_key')
    result3 = simple_clac.get('test_key', layer_name='alpha')
    assert result1 is result2 is result3
    assert result1 == 'test_value_alpha'

    # cfg = CLAC(SimpleLayer('test', {'test_key': "test_value"}))
    # assert 'test' in cfg
    # assert 'test_key' in cfg.names
    # rs1 = cfg['test_key']
    # rs2 = cfg.get('test_key', layer_name='test')
    # assert rs1 is rs2 and rs1 == 'test_value'


def test_multi_layer_priority(clac_layers):
    alpha, beta, _ = clac_layers
    cfg = CLAC(alpha, beta)

    assert 'alpha' in cfg
    assert 'beta' in cfg
    assert 'test_key' in cfg.names
    assert 'beta_secret' in cfg.names
    assert cfg['test_key'] == 'test_value_alpha'
    assert cfg.get('test_key', layer_name='beta') == 'test_value_beta'
    assert cfg['beta_secret'] == 'fghij'


def test_remove_layer(clac_layers):
    alpha, beta, _ = clac_layers
    cfg = CLAC(alpha, beta)

    assert cfg['beta_secret'] == 'fghij'
    cfg.remove_layer('beta')
    with raises(NoConfigKey):
        _ = cfg['beta_secret']


def test_insert_layer(clac_layers):
    alpha, beta, gamma = clac_layers
    expected_name_list = []

    cfg = CLAC(gamma)
    expected_name_list.append('gamma')
    assert list(cfg.layers) == expected_name_list

    cfg.insert_layers(beta)
    expected_name_list.insert(0, 'beta')
    assert list(cfg.layers) == expected_name_list

    cfg.insert_layers(beta, alpha)
    expected_name_list.insert(1, 'alpha')
    assert list(cfg.layers) == expected_name_list

    fake_beta = SimpleLayer('beta', {})
    with raises(LayerOverwriteError):
        cfg.insert_layers(fake_beta)

    cfg.insert_layers(fake_beta, raise_on_replace=False)

    assert cfg.layers == {
        'beta': fake_beta,
        'alpha': alpha,
        'gamma': gamma,
    }


def test_add_layer(clac_layers):
    alpha, beta, _ = clac_layers
    cfg = CLAC(alpha)

    assert cfg['test_key'] == 'test_value_alpha'
    with raises(NoConfigKey):
        _ = cfg['beta_secret']
    with raises(MissingLayer):
        cfg.get('test_key', layer_name='beta')

    cfg.add_layers(beta)

    assert cfg['test_key'] == 'test_value_alpha'
    assert cfg['beta_secret'] == 'fghij'
    assert cfg.get('test_key', layer_name='beta') == 'test_value_beta'


def test_names_property(clac_layers):
    simple_clac = CLAC(*clac_layers)
    assert {
        'test_key',
        'alpha_secret',
        'beta_secret',
        'unique',
        'gamma_secret',
    } == simple_clac.names


def test_build_lri(clac_layers):
    simple_clac = CLAC(*clac_layers)
    assert simple_clac.build_lri() == {
        ('alpha', 'test_key'),
        ('alpha', 'alpha_secret'),
        ('alpha', 'unique'),
        ('beta', 'beta_secret'),
        ('gamma', 'gamma_secret'),
    }


@mark.xfail
def test_build_reverse_lri(clac_layers):
    simple_clac = CLAC(*clac_layers)
    assert simple_clac.build_lri(True) == {
        ('test_key', 'alpha'),
        ('alpha_secret', 'alpha'),
        ('unique', 'alpha'),
        ('beta_secret', 'beta'),
        ('gamma_secret', 'gamma'),
    }


def test_get_default(clac_layers):
    simple_clac = CLAC(*clac_layers)
    default = object()
    assert simple_clac.get('missingkey', default=default) is default


def test_assert_immutable(clac_layers):
    simple_clac = CLAC(*clac_layers)
    with raises(ImmutableLayer):
        simple_clac['test_key'] = 'hello'
    with raises(ImmutableLayer):
        clac_layers[0]['test_key'] = 'Hello'
    with raises(ImmutableLayer):
        simple_clac.setdefault('test_key')


def test_mutate_existing_key(mutable_layers):
    mutable_clac = CLAC(*mutable_layers)

    unique = object()

    assert mutable_clac.get('test_key') == 'test_value_alpha'
    assert mutable_clac.get('test_key', layer_name='beta') == 'test_value_beta'
    mutable_clac['test_key'] = unique
    assert mutable_clac.get('test_key') == 'test_value_alpha'
    assert mutable_clac.get('test_key', layer_name='beta') is unique


def test_add_new_key(mutable_layers):
    mutable_clac = CLAC(*mutable_layers)

    unique = object()
    default = object()

    assert mutable_clac.get('new_key', default=default) is default
    assert mutable_clac.get('new_key', layer_name='beta', default=default) is default
    mutable_clac['new_key'] = unique
    assert mutable_clac.get('new_key', default=default) is unique
    assert mutable_clac.get('new_key', layer_name='beta', default=default) is unique


def test_setdefault(mutable_layers):
    mutable_clac = CLAC(*mutable_layers)

    unique = object()
    default = object()

    assert mutable_clac.get('new_key', default=default) is default
    assert mutable_clac.get('new_key', layer_name='beta', default=default) is default
    mutable_clac.setdefault('new_key', unique)
    assert mutable_clac.setdefault('new_key', 'acbde') is unique
    assert mutable_clac.get('new_key', default=default) is unique
    assert mutable_clac.get('new_key', layer_name='beta', default=default) is unique


def test_get_callback(clac_layers):
    simple_clac = CLAC(*clac_layers)

    assert simple_clac.get('unique', callback=int) == 123456789
    assert simple_clac.get('missing', default='not a list', callback=list) == 'not a list'


def test_no_key():
    clac = CLAC()
    with raises(ValueError):
        _ = clac['']


def test_bad_layer():
    clac = CLAC()
    clac.remove_layer('none')
    with raises(MissingLayer):
        clac.remove_layer('none', error_ok=False)

    with raises(MissingLayer):
        clac.get('key', layer_name='none')


def test_resolve(clac_layers):
    simple_clac = CLAC(*clac_layers)

    assert simple_clac.resolve('beta_secret') == ('beta', 'fghij')
    with raises(NoConfigKey):
        simple_clac.resolve('missing.key')


def test_layers(clac_layers):
    simple_clac = CLAC(*clac_layers)
    expected_lookup = {layer.name: layer for layer in clac_layers}
    assert simple_clac.layers == expected_lookup
