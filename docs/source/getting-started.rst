Getting Started
===============

First we install the library:

.. code-block:: bash

   pip install clac

Next, we need to prepare each of our layers:

.. code-block:: python

   from clac import CLAC, DictLayer, DictStructure, EnvLayer

   # Get the dicts for each of the layers

   # rc-style files are usually flat keys, which could have dots in their names.
   # Google .pylintrc or .coveragerc for examples of rc-style config files.
   rcfile = {
       'lingua': 'franca',
       'salt.pepper': 'oregano',
       'foo': 'bar',
   }
   # Create the layer with a recognizable name
   rc_layer = DictLayer('rcfile', rcfile)

   # We can import toml or json directly into nested python dictionaries.
   # For this example we will assume that the following dict was imported
   # earlier.
   toml_dict = {
       'foo': 'baz',
       'spam': {
           'ham': 'eggs',
       },
       'salt': {
           'pepper': 'cayenne',
       },
   }
   # This time, we need to split the names by the dots, since these dicts have
   # a nested-dict structure.
   toml_layer = DictLayer('tomlfile', toml_dict, dot_strategy=DictStructure.Split)

   # For environment variables, we can instatiate a layer directly
   env_layer = EnvLayer('env')

   # Now we can create the container for all of the layers
   config = CLAC(rc_layer, toml_layer, env_layer)

   # We could also build the object incrementally, separate from instatiation.
   # Adding the rcfile layer first means that values from that rcfile values
   # will override competing values from the toml layer.
   config = CLAC()
   config.add_layers(rc_layer)
   # We can still add multiple layers at once.
   config.add_layers(toml_layer, env_layer)

Now, we can check the various config entries.

.. code-block:: python

   # 'foo' is found in the rcfile first, so we get 'bar' instaed of 'baz'
   assert config['foo'] == 'bar'
   # But we can double-check the toml file if we want, using the name of the
   # layer we want.
   assert config.get('foo', layer_name='tomlfile') == 'baz'

   # 'spam' is not found in the rcfile, so the CLAC checks the tomlfile
   assert config['spam'] == {'ham': 'eggs'}

   # Be careful when searching on partial keys, since flat DictLayers cannot
   # support partial matching:

   # 'salt' would be a partial match for rcfile, so toml file value is used
   assert config['salt'] == {'pepper': 'cayenne'}
   # 'salt.pepper' has an exact match in the rcfile, so we get that value
   # before the toml file.
   assert config['salt.pepper'] == 'oregano

   # get() supports defaults and post-retrieval processing, but not at the same
   # time.  Default values are *not* processed with the callback.

   # Here, we set the callback to str, but still get an int, because the value
   # was not found, and the callback was never executed.  This return the
   # default value as-is.
   assert config.get('missing', default=123, callback=str) == 123
