import re
pattern = '(?P<cmd>\w+)[ (?P<arg>\S+)]?\r\n'
request = 'USER latin\r\n'
rs = re.match(pattern, request)
if rs:
    rs = rs.groupdict()
    cmd = rs.get('cmd')
    arg = rs.get('arg')
    print(cmd, arg)
else:
    print('false')
