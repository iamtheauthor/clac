Getting Started
===============

First we install (virtual environments are recommended, but up to the user)

.. code-block:: bash

   pip install clac

Next, we need to prepare each of our layers:

.. code-block:: python

   from clac import CLAC, DictLayer, DictStructure, EnvLayer

   # Get the dicts for each of the layers

   # rc-style files are usually flat keys, which could have dots in their names
   rcfile = {
       'lingua': 'franca',
       'salt.pepper': 'oregano',
       'foo': 'bar',
   }
   # Create the layer with a recognizable name
   rc_layer = DictLayer('rcfile', rcfile)

   # We can import toml or json directly into nested python dictionaries
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


   # Now we can create the container for all of the layers
   config = CLAC(rc_layer, toml_layer)
   # We could also build the object incrementally
   config = CLAC()
   # Adding the rcfile layer first means that values from that rcfile values
   # will override competing values from the toml layer.
   config.add_layers(rc_layer)
   config.add_layers(toml_layer)

   # Now, we can check the various config entries

   # 'foo' is found in the rcfile first, so we get 'bar' instaed of 'baz'
   assert config['foo'] == 'bar'
   # But we can double-check the toml file if we want, using the name of the
   # layer we want.
   assert config.get('foo', layer_name='tomlfile') == 'baz'
   # 'spam' is not found in the rcfile, so the CLAC checks the tomlfile
   assert config['spam'] == {'ham': 'eggs'}
   # Be careful when searching on partial keys, since flat DictLayers cannot
   # support partial matching
   assert config['salt'] == {'pepper': 'cayenne'}
   assert config['salt.pepper'] == 'oregano
   # get() supports defaults and post-retrieval processing, but not at the same
   # time.  Default values are not processed with the callback.
   assert config.get('missing', default=123, callback=str) == 123


