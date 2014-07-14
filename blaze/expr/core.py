from __future__ import absolute_import, division, print_function

import toolz

from ..dispatch import dispatch

__all__ = ['Expr', 'Scalar', 'discover']


def _str(s):
    """ Wrap single quotes around strings """
    if isinstance(s, str):
        return "'%s'" % s
    else:
        return str(s)


class Expr(object):
    @property
    def args(self):
        return tuple(getattr(self, slot) for slot in self.__slots__)

    def isidentical(self, other):
        return type(self) == type(other) and self.args == other.args

    __eq__ = isidentical

    def __hash__(self):
        return hash((type(self), self.args))

    def __str__(self):
        return "%s(%s)" % (type(self).__name__, ', '.join(map(_str, self.args)))

    def __repr__(self):
        return str(self)

    def traverse(self):
        """ Traverse over tree, yielding all subtrees and leaves """
        yield self
        traversals = (arg.traverse() if isinstance(arg, Expr) else [arg]
                        for arg in self.args)
        for trav in traversals:
            for item in trav:
                yield item

    def subs(self, d):
        """ Substitute terms in the tree

        >>> from blaze.expr.table import TableSymbol
        >>> t = TableSymbol('t', '{name: string, amount: int, id: int}')
        >>> expr = t['amount'] + 3
        >>> expr.subs({3: 4, 'amount': 'id'}).isidentical(t['id'] + 4)
        True
        """
        return subs(self, d)

    def resources(self):
        return toolz.merge([arg.resources() for arg in self.args
                                            if isinstance(arg, Expr)])



def subs(o, d):
    """ Substitute values within data structure

    >>> subs(1, {1: 2})
    2

    >>> subs([1, 2, 3], {2: 'Hello'})
    [1, 'Hello', 3]
    """
    try:
        if o in d:
            d = d.copy()
            o = d.pop(o)
    except TypeError:
        pass
    return _subs(o, d)


@dispatch((tuple, list), dict)
def _subs(o, d):
    return type(o)([subs(arg, d) for arg in o])


@dispatch(Expr, dict)
def _subs(o, d):
    """

    >>> from blaze.expr.table import TableSymbol
    >>> t = TableSymbol('t', '{name: string, balance: int}')
    >>> subs(t, {'balance': 'amount'}).columns
    ['name', 'amount']
    """
    newargs = [subs(arg, d) for arg in o.args]
    return type(o)(*newargs)


@dispatch(object, dict)
def _subs(o, d):
    """ Private dispatched version of ``subs``

    >>> subs('Hello', {})
    'Hello'
    """
    return o


class Scalar(Expr):
    pass


@dispatch(Expr)
def discover(expr):
    return expr.dshape
