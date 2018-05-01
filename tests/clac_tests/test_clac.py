import pathlib
# import sys
from typing import Iterable

from pytest import raises

# sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from clac import (  # noqa: E402
    CLAC, BaseConfigLayer, NoConfigKey, MissingLayer
)

__here__ = pathlib.Path(__file__).resolve().parent


class SimpleLayer(BaseConfigLayer):
    def __init__(self, name, data):
        super().__init__(name)
        self.data = data

    def get(self, key):
        return self.data[key]

    def __contains__(self, name: str) -> bool:
        return name in self.data

    @property
    def names(self) -> Iterable[str]:
        return self.data.keys()


def test_get_from_one_layer():
    cfg = CLAC(SimpleLayer('test', {'test_key': "test_value"}))
    assert 'test' in cfg
    assert 'test_key' in cfg.names
    rs1 = cfg.get('test_key')
    rs2 = cfg.get('test_key', layer_name='test')
    assert rs1 is rs2 and rs1 == 'test_value'


def test_multi_layer_priority():
    alpha_dict = {'test_key': 'test_value_alpha'}
    beta_dict = {
        'test_key': 'test_value_beta',
        'secret_key': 'beta_secret'
    }
    alpha = SimpleLayer('alpha', alpha_dict)
    beta = SimpleLayer('beta', beta_dict)
    cfg = CLAC(alpha, beta)

    assert 'alpha' in cfg
    assert 'beta' in cfg
    assert 'test_key' in cfg.names
    assert 'secret_key' in cfg.names
    assert cfg.get('test_key') == 'test_value_alpha'
    assert cfg.get('test_key', layer_name='beta') == 'test_value_beta'
    assert cfg.get('secret_key') == 'beta_secret'


def test_remove_layer():
    alpha_dict = {'test_key': 'test_value_alpha'}
    beta_dict = {
        'test_key': 'test_value_beta',
        'secret_key': 'beta_secret'
    }
    alpha = SimpleLayer('alpha', alpha_dict)
    beta = SimpleLayer('beta', beta_dict)
    cfg = CLAC(alpha, beta)

    assert cfg.get('secret_key') == 'beta_secret'
    cfg.remove_layer('beta')
    with raises(NoConfigKey):
        cfg.get('secret_key')


def test_add_layer():
    alpha_dict = {
        'test_key': 'test_value_alpha',
        'alpha_secret': 'abcde',
    }
    beta_dict = {
        'test_key': 'test_value_beta',
        'beta_secret': 'fghij',
    }
    alpha = SimpleLayer('alpha', alpha_dict)
    beta = SimpleLayer('beta', beta_dict)
    cfg = CLAC(alpha)

    assert cfg.get('test_key') == 'test_value_alpha'
    with raises(NoConfigKey):
        cfg.get('beta_secret')
    with raises(MissingLayer):
        cfg.get('test_key', layer_name='beta')

    cfg.add_layers(beta)

    assert cfg.get('test_key') == 'test_value_alpha'
    assert cfg.get('beta_secret') == 'fghij'
    assert cfg.get('test_key', layer_name='beta') == 'test_value_beta'


def test_names_property():
    alpha_dict = {
        'test_key': 'test_value_alpha',
        'alpha_secret': 'abcde',
    }
    beta_dict = {
        'test_key': 'test_value_beta',
        'beta_secret': 'fghij',
    }
    alpha = SimpleLayer('alpha', alpha_dict)
    beta = SimpleLayer('beta', beta_dict)
    cfg = CLAC(alpha, beta)

    assert set((
        'test_key',
        'alpha_secret',
        'beta_secret'
    )) == cfg.names


def test_lri():
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

    cfg = CLAC(alpha, beta, gamma)

    assert cfg.get_layer_resolution() == set([
        ('alpha', 'test_key'),
        ('alpha', 'alpha_secret'),
        ('alpha', 'unique'),
        ('beta', 'beta_secret'),
        ('gamma', 'gamma_secret'),
    ])
