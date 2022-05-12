import socket
import threading
import argparse

# Handling incoming connection of clients
def accept_incoming_connection():
    while True:
        client, address = SERVER.accept()
        print("%s:%s подключился к серверу." % address)
        addresses[client] = address
        threading.Thread(target=handle_client, args=(client, )).start()

# Handle a single client connection
def handle_client(client):
    name = ""
    prefix = ""

    while True:
        msg = client.recv(BUFSIZE)

        if not msg is None:
            msg = msg.decode("utf-8")
        
        if msg == "":
            msg = "{QUIT}"
        
        # Avoid messages before registering
        if msg.startswith("{ALL}") and name:
            new_msg = msg.replace("{ALL}", "{MSG}" + prefix)
            send_message(new_msg, broadcast=True)
            continue
        
        if msg.startswith("{REGISTER}"):
            name = msg.split("}")[1]
            welcome = '{MSG}Добро пожаловать %s!' % name
            send_message(welcome, destination=client)
            msg = '{MSG}%s присоединился к чату!' % name
            send_message(msg, broadcast=True)
            clients[client] = name
            prefix = name + ": "
            send_client()
            continue
        
        if msg == "{QUIT}":
            client.close()
            try:
                del clients[client]
            except KeyError:
                pass

            if name:
                send_message("{MSG}%s вышел(а) из чата." % name, broadcast=True)
                send_client()
            break
            
        if not name:
            continue

        # Send private message or unknow message
        try:
            msg_params = msg.split("}")
            dest_name = msg_params[0][1:]
            dest_sock = find_client_socket(dest_name)
            if dest_sock:
                send_message(msg_params[1], prefix=prefix, destination=dest_sock)
            else:
                print("Неверный пункт назначения. %s" % msg)
        except:
            print("Ошибка разбора сообщения: %s" % msg)

def find_client_socket(name):
    for cli_sock, cli_name in clients.items():
        if cli_name == name:
            return cli_sock
    return None

def send_client():
    send_message("{CLIENTS}" + get_clients_name(), broadcast=True)

def get_clients_name(separator='|'):
    names = []
    for _, name in clients.items():
        names.append(name)
    return separator.join(names)        

def send_message(msg, prefix="", destination=None, broadcast=False):
    send_msg = bytes(prefix + msg, "utf-8")
    if broadcast:
        # Send message to all client
        for sock in clients:
            sock.send(send_msg)
    else:
        if destination is not None:
            destination.send(send_msg)


clients = {}
addresses = {}

parser = argparse.ArgumentParser(description="Чат-сервер")

# Input address host 
parser.add_argument(
    '--host',
    help='Host IP',
    default='127.0.0.1'
)

# Input port
parser.add_argument(
    '--port',
    help='Port Number',
    default='2112',
)

server_args = parser.parse_args()

HOST = server_args.host
PORT = int(server_args.port)
BUFSIZE = 2048
ADDR = (HOST, PORT)

stop_server = False

# IPv4 and TCP protocol
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.bind(ADDR)

if __name__ == '__main__':
    try:
        SERVER.listen(5)
        print("Сервер запущен на {}:{}".format(HOST, PORT))
        print("Ожидание подключения...")
        ACCEPT_THREAD = threading.Thread(target=accept_incoming_connection)
        ACCEPT_THREAD.start()
        ACCEPT_THREAD.join()
        SERVER.close()

    except KeyboardInterrupt:
        print("Закрытие...")
        ACCEPT_THREAD.interrupt()
        