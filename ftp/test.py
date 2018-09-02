with open('test', 'r+') as f:
    print(f.seekable())
    f.seek(1000)
    f.write('sdfa')
    f.flush()
    f.seek(0)
    print(f.read())
