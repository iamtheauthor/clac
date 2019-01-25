from pytest import fixture, raises

from clac import DictLayer, DictStructure, NoConfigKey


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


def test_init():
    DictLayer('name')
    with raises(TypeError):
        DictLayer('name', 'not a mapping')
    with raises(ValueError):
        DictLayer('name', dot_strategy='not a DictStrucure')


def test_blank_mutable():
    layer = DictLayer('name', mutable=True)

    unique = object()
    unique2 = object()
    default = object()

    assert layer.get('new_key', default=default) is default
    with raises(NoConfigKey):
        _ = layer['new_key.subkey']
    assert layer.setdefault('new_key', unique) is unique
    layer['new_key.subkey'] = unique2
    assert layer.get('new_key', default=default) is unique
    assert layer['new_key.subkey'] is unique2


def test_mutable_split():
    layer = DictLayer('name', mutable=True, dot_strategy=DictStructure.Split)

    unique = object()
    default = object()

    assert layer.get('new_key.subkey', default=default) is default
    layer.setdefault('new_key', {})
    assert layer.setdefault('new_key.subkey', unique) is unique

    assert layer['new_key'] == {'subkey': unique}


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
