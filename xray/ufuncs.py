"""xray specific universal functions

Handles unary and binary operations for the following types, in ascending
priority order:
- scalars
- numpy.ndarray
- dask.array.Array
- xray.Variable
- xray.DataArray
- xray.Dataset
- xray.core.groupby.GroupBy

Once NumPy 1.10 comes out with support for overriding ufuncs, this module will
hopefully no longer be necessary.
"""
import numpy as _np

from .core.variable import Variable as _Variable
from .core.dataset import Dataset as _Dataset
from .core.dataarray import DataArray as _DataArray
from .core.groupby import GroupBy as _GroupBy

from .core.pycompat import dask_array_type as _dask_array_type
from .core.ops import _dask_or_eager_func


_xray_types = (_Variable, _DataArray, _Dataset, _GroupBy)
_dispatch_order = (_np.ndarray, _dask_array_type) + _xray_types


def _dispatch_priority(obj):
    for priority, cls in enumerate(_dispatch_order):
        if isinstance(obj, cls):
            return priority
    return -1


def _create_op(name):

    def func(*args, **kwargs):
        new_args = args
        f = _dask_or_eager_func(name)
        if len(args) > 2 or len(args) == 0:
            raise TypeError('cannot handle %s arguments for %r' %
                            (len(args), name))
        elif len(args) == 1:
            if isinstance(args[0], _xray_types):
                f = args[0]._unary_op(func)
        else:  # len(args) = 2
            p1, p2 = map(_dispatch_priority, args)
            if p1 >= p2:
                if isinstance(args[0], _xray_types):
                    f = args[0]._binary_op(func)
            else:
                if isinstance(args[1], _xray_types):
                    f = args[1]._binary_op(func, reflexive=True)
                    new_args = tuple(reversed(args))
        res = f(*new_args, **kwargs)
        if res is NotImplemented:
            raise TypeError('%r not implemented for types (%r, %r)'
                            % (name, type(args[0]), type(args[1])))
        return res

    func.__name__ = name
    doc = getattr(_np, name).__doc__
    func.__doc__ = ('xray specific variant of numpy.%s. Handles '
                    'xray.Dataset, xray.DataArray, xray.Variable, '
                    'numpy.ndarray and dask.array.Array objects with '
                    'automatic dispatching.\n\n'
                    'Documentation from numpy:\n\n%s' % (name, doc))
    return func


__all__ = """logaddexp logaddexp2 conj exp log log2 log10 log1p expm1 sqrt
             square sin cos tan arcsin arccos arctan arctan2 hypot sinh cosh
             tanh arcsinh arccosh arctanh deg2rad rad2deg logical_and
             logical_or logical_xor logical_not maximum minimum fmax fmin
             isreal iscomplex isfinite isinf isnan signbit copysign nextafter
             ldexp fmod floor ceil trunc degrees radians rint fix angle real
             imag fabs sign frexp fmod
             """.split()

for name in __all__:
    globals()[name] = _create_op(name)
