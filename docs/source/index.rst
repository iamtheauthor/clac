.. clac documentation master file, created by
   sphinx-quickstart on Tue May  1 12:57:18 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CLAC!
================

.. note::Please note that the documentation is not complete, and any help would be
   welcome.  Different ideas about how to complete or structure the docs would
   be welcome, as well as pull requests toward completing that goal.

   If you would like to contribute to this goal, please see the contribution
   guidelines here

What is CLAC?
-------------

CLAC is a multi-level configuration management library for use by applications
which require multi-source configuration, such as multiple config files (which
could have priority overriding based on location), environment variables,
command-line parameters, and default configuration shipped with the application
itself.

The theory behind the tool is that the each of the configuration sources is a
layer, and each layer has a priority against the other layers, e.g.
command-line options should override competing environment variables.  The
layers are collected into a single object, and a single function call will
search for the proper value in each layer, returning the highest priority
value.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   api-reference
   environment-setup

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
