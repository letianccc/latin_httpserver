from httpserver.entity.exception import *

def raise_():
    raise Forbidden

def f():
    try:
        pass
        raise_()
    except NotFound:
        print('not found')
    except Forbidden:
        print('forbid')

f()
