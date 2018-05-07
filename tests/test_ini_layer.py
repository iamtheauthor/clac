import pathlib

from pytest import fixture

from clac.layers import IniLayer

__here__ = pathlib.Path(__file__).resolve().parent
__ini__ = __here__ / 'test_ini_layer.ini'


@fixture(name='testlayer')
def fixture_inilayer():
    yield IniLayer('test_ini', __ini__)


def test_inilayer_iter(testlayer):
    assert [
        'section.option',
        'section.subsect.subopt'
    ] == [opt for opt in testlayer]


def test_inilayer_len(testlayer):
    assert len(testlayer) == 2


def test_inilayer_getitem(testlayer):
    assert testlayer['section.option'] == 'value'
    assert testlayer.get('section.subsect.subopt') == 'subvalue'


def test_inilayer_names(testlayer):
    assert {
        'section.option',
        'section.subsect.subopt'
    } == testlayer.names
