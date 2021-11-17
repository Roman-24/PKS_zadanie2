
import socket
import threading
import time

# ----- KONSTANTY -----

# universal
RECV_FROM = 1500
FORMAT = "utf-8"
TIMEOUT = 20

# flags
START = 0
SYN = 1
ACK = 2
NACK = 4
KA = 16
RST = 32
TEXT = 64
FILE = 128

# server site
KEEPALIVE_REQUEST = "k"

# client site
CLIENT_INTERVAL = 10
thread_status = True

# ----- POMOCNE VECI -----
class Mypacket:

    def __init__(self, flag, number, size, crc, data):
        self.flag = flag
        self.number = number
        self.size = size
        self.crc = crc
        self.data = data

    def __bytes__(self):
        temp = self.flag.to_bytes(1, 'big') + self.number.to_bytes(3, 'big') + self.size.to_bytes(2, 'big') + self.crc.to_bytes(2, 'big') + self.data.encode(FORMAT)
        return temp

# ----- POMOCNE FUNKCIE -----
def packet_reconstruction(packet_as_bajty):

    flag = int.from_bytes(packet_as_bajty[0:1], 'big')
    number = int.from_bytes(packet_as_bajty[1:4], 'big')
    size = int.from_bytes(packet_as_bajty[4:6], 'big')
    crc = int.from_bytes(packet_as_bajty[6:8], 'big')
    data = packet_as_bajty[8:].decode(FORMAT)

    packet_as_obj = Mypacket(flag, number, size, crc, data)
    return packet_as_obj


# ----- SERVER SITE FUNCS -----

# funkcia sluzi ako spustitel serveru
# to znamena ze si vyziada udaje potrebne na spustenie serveru (ip a port)
#
def mode_server():

    address = "127.0.0.1"
    #address = input("IP address of server: ")
    port = int(1234)
    #port = int(input("Server port: "))
    addr_tuple = (address, port)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(addr_tuple)

    try:
        # cakanie na ziadost o spojenie SYN od klinta
        data, address = server_socket.recvfrom(RECV_FROM)
        data = packet_reconstruction(data)

        # ak prisla ziadost o spojenie SYN
        if data.flag == SYN:

            # server posle klientovy SYN ACK
            initialization_packet = Mypacket(SYN + ACK, 0, 0, 0, "")
            server_socket.sendto(initialization_packet.__bytes__(), address)

            # cakanie na potvrdenie spojenia ACK od klienta
            data, address = server_socket.recvfrom(RECV_FROM)
            data = packet_reconstruction(data)

            # ak prislo ACK tak spojenie je active
            if data.flag == ACK:
                print(f"Established connection with {address}, port: {port}")
                server_site(server_socket, address)
            else:
                print(f"Established connection failed")
                return

    except OSError:
        print(f"Established connection failed")
        return

    pass

def server_site(server_socket, address):

    while(True):

        print("1 for continue as server")
        print("2 for switching role")
        print("x for exit")
        client_input = input()

        if client_input == "x":
            return

        elif client_input == "2":
            switch_users(server_socket, address)
        elif client_input == "1":

            print("Server is running..")

            try:
                # podla zadanie server preveruje spojenie kazdych 5-20s
                server_socket.settimeout(TIMEOUT)

                # pocuvanie na strane serveru
                while True:

                    # keep alive
                    while True:
                        data = server_socket.recvfrom(RECV_FROM)
                        data = packet_reconstruction(data)

                        # ak prisla keep alive poziadavka
                        if data.flag == KEEPALIVE_REQUEST:
                            acceptation_packet = Mypacket("a", 0, 0, 0, "")
                            server_socket.sendto(acceptation_packet, address)
                            break
                        else:
                            break

                    # prijatie spravy
                    number_of_packets = data.data
                    print(f"Incoming data will consist of {number_of_packets} packets\n")

                    # z toho co sme prijali chceme vytiahnut typ spravy bud to bude
                    # transport spravy alebo transport file
                    #
                    # ak bude server prijimat subor
                    if data.flag == "e":
                        server_as_receiver(number_of_packets, server_socket, "f")
                    # ak bude server prijimat text message
                    elif data.flag == "b":
                        server_as_receiver(number_of_packets, server_socket, "m")

                    break
                pass

            except socket.timeout:
                print("Client is inactive..\nShutting down..")
                server_socket.close()
                return
        else:
            print("Wrong input, maybe try it again!")
        pass
    pass

def server_as_receiver(number_of_packets_com, server_socket, type):

    print("Server receiving text message or file..")

    received_packets_total = 0
    number_of_received_packets = 0
    full_message = []

    while True:

        while True:
            if number_of_received_packets == int(number_of_packets_com):
                break

            data, address = server_socket.recvfrom(RECV_FROM)


    pass



# ----- CLIENT SITE FUNCS -----

def mode_client():

    print("Client is here")

    while True:

        address = "127.0.0.1"
        #address = input("IP address of server: ")
        port = int(1234)
        #port = int(input("Client port: "))
        server_addr_tuple = (address, port)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # bin ???

        try:
            client_socket.settimeout(TIMEOUT)

            # poslanie poziadavky na spojenie SYN
            initialization_packet = Mypacket(SYN, 0, 0, 0, "")
            client_socket.sendto(initialization_packet.__bytes__(), server_addr_tuple)

            # cakanie na SYN ACK od serveru
            data, address = client_socket.recvfrom(RECV_FROM)
            data = packet_reconstruction(data)

            # ak od serveru prislo potvrdenie spojenia SYN ACK
            if data.flag == SYN + ACK:

                # tak posle potvrdenie aj klient teda posle ACK
                initialization_packet = Mypacket(ACK, 0, 0, 0, "")
                client_socket.sendto(initialization_packet.__bytes__(), server_addr_tuple)

                print("Connected to address:", server_addr_tuple)
                client_site(client_socket, server_addr_tuple)

        except (socket.timeout, socket.gaierror, OSError, Exception) as err:
            print(err)
            print("Connection not working!\nMaybe try it again..")
            client_socket.close()
            return
            # continue

def client_site(client_socket, server_addr_tuple):
    global thread_status
    thread = None

    while True:
        print("x for exit")
        print("1 for text message")
        print("2 for file message")
        print("3 for keep alive ON")
        print("4 for keep alive OFF")
        print("5 for switching role")
        client_input = input()

        if client_input == "x" or client_input == "1" or client_input == "2" or client_input == "5":
            if thread is not None:
                thread_status = False
                thread.join()

            if client_input == "x":
                return

            elif client_input == "1":
                client_as_sender(client_socket, server_addr_tuple, "m")
            elif client_input == "2":
                client_as_sender(client_socket, server_addr_tuple, "f")

            elif client_input == "5":
                switch_users(client_socket, server_addr_tuple)

        elif client_input == "3":
            print("Keep alive ON")
            thread_status = True
            thread = start_thread(client_socket, server_addr_tuple)

        elif client_input == "4":
            if thread is not None:
                print("Keep alive OFF")
                thread_status = False
                thread.join()

        else:
            print("Wrong input, maybe try it again!")

    pass

def client_as_sender(client_socket, server_addr_tuple, type):

    pass

# ----- OTHERS FUNC -----
def switch_users(client_socket, server_addr_tuple):

    pass

def start_thread(client_socket, server_addr_tuple):
    lock = threading.Lock()
    thread = threading.Thread(target=keep_alive, args=(client_socket, server_addr_tuple, lock))
    thread.daemon = True
    thread.start()
    return thread

def keep_alive(client_socket, server_addr_tuple, lock):

    while True:

        if not thread_status:
            return

        with lock:
            client_socket.sendto(str.encode(" "), server_addr_tuple)
            data = client_socket.recv(RECV_FROM)
            information = str(data.decode())

            if information == "":
                print("Connection is working..")
            else:
                print("Connection ended")
                break
            time.sleep(CLIENT_INTERVAL)
    pass

def main():
    print("Pycharm starting..")

    device_type = input("Pre mod server zadaj: s \nPre mod client zadaj: c \nPre koniec zadaj: x\n")

    while device_type != "x":

        if device_type == "s":
            mode_server()
        elif device_type == "c":
            mode_client()
        else:
            print("Nespravna volba")

        device_type = input("Pre mod server zadaj: s \nPre mod client zadaj: c \nPre koniec zadaj: x\n")

if __name__ == "__main__":
    main()
#end
