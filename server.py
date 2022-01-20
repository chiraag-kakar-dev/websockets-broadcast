import socket
s=socket.socket()
print('socket created')

s.bind(('localhost',9999))
s.listen(3)
print('waiting for connections')

while True:
    c, addr=s.accept()
    print(c)
    name=c.recv(1024).decode()
    print('connected with ',addr,name)
    name=c.recv(1024).decode()
    c.send(bytes('welcome my boy','utf-8'))
    c.close()
