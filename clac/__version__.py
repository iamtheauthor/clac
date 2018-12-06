# Copyright 2018 Wesley Van Melle <van.melle.wes@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Version specification for the clac package

The `__major__`, `__minor__`, and `__patch__` attributes follow the semantic
version spec, in X.Y.Z format.  `__patch__` may be auto-incremented by
build tools in the future, but `__major__` and `__minor__` will only be
incremented manually.

`__version__` allows for API compatibility comparison, and is defined as a
2-tuple: `(__major__, __minor__).`

`__release__` is the semantic version compatible string in 'X.Y.Z' format.
"""

__major__: int = 1
__minor__: int = 1
__patch__: int = 0

__version__ = (__major__, __minor__)
__release__: str = f'{__major__}.{__minor__}.{__patch__}'
