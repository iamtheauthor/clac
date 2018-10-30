import os

from clac import EnvLayer


def test_env_get():
    layer = EnvLayer('env')

    os.environ['SOME_SECRET_KEY'] = '1234567890'
    assert layer['some.secret.Key'] == '1234567890'
    assert layer.get('some.secret.key') == '1234567890'
    assert layer.get('this.does.not.exist') is None


def test_env_prefix():
    layer = EnvLayer('env', prefix='myprefix')

    os.environ['MYPREFIX_SOME_SECRET_KEY'] = '9876543210'
    assert layer['some.secret.Key'] == '9876543210'
    assert layer.get('some.secret.key') == '9876543210'
    assert layer.get('this.does.not.exist') is None
