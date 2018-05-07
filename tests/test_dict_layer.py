from pytest import fixture

from clac import DictLayer, DictStructure


@fixture(name='flat_layer')
def fixture_flat_dict_layer():
    yield DictLayer(
        'test-dict',
        {
            'key1': 123,
            "flat.dot.key": 'abc'
        }
    )


@fixture(name='dotted_layer')
def fixture_dotted_dict_layer():
    yield DictLayer(
        'test-dict',
        {
            'key1': 123,
            "flat": {
                "dot": {
                    "key": 'abc'
                }
            }
        },
        dot_strategy=DictStructure.Split
    )


def test_flat_len_dictlayer(flat_layer):
    assert len(flat_layer) == 2


def test_flat_iter_dictlayer(flat_layer):
    assert sorted([
        'key1',
        'flat.dot.key'
    ]) == sorted([key for key in flat_layer])


def test_flat_names_dictlayer(flat_layer):
    assert {
        "key1",
        "flat.dot.key"
    } == flat_layer.names


def test_flat_getitem_dictlayer(flat_layer):
    assert flat_layer['key1'] == 123
    assert flat_layer['flat.dot.key'] == 'abc'


def test_dotted_getitem_dictlayer(dotted_layer):
    assert dotted_layer['key1'] == 123
    assert dotted_layer['flat.dot.key'] == 'abc'


def test_dotted_len_dictlayer(dotted_layer):
    assert len(dotted_layer) == 2


def test_dotted_iter_dictlayer(dotted_layer):
    assert sorted([
        'key1',
        'flat.dot.key'
    ]) == sorted([key for key in dotted_layer])


def test_dotted_names_dictlayer(dotted_layer):
    assert {
        "key1",
        "flat.dot.key"
    } == dotted_layer.names
