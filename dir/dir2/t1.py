# x = 'x'
# print('t1', x)
# import t2
# print('t1', t2.a)
# print('t1', t2.b)

x = 'x'
print('t1', x)
from t2 import a
print('t1', a)
from t2 import b
print('t1', b)


# x = 'x'
# print('t1', x)
# from main import a
# print('t1', a)
# from main import b
# print('t1', b)