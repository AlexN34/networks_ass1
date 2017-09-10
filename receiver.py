import pickle
import socket
import sys


class Receiver:
    # Receiver ? match rec seq-num ? good (keep packet) : otherwise, discard
    # packet (or buffer) -> send back ack with ack number 10 (seq is number of
    # thing it's expecting)
    # if received a good packet, Receiver sends Sender an ack indicating next
    # packet with number 10 + len(data)
    #
    # you need to create this
    # receiver needs to have a sequence number so it can deal with
    # out-of-order packets
    # receiver receives stp_packet ad the writes the data inside the packet
    connection_socket = socket.create_connection(socket.SOCK_DGRAM)
    buffer_size = 4096

    def receive_packet(self):
        data, addr = self.connection_socket.recvfrom(buffer_size)
        stp_packet = pickle._loads(data)  # data is property of stp_packet


n_expected_args = 3
if __name__ == "__main__":
    # do setup when run
    # python receiver.py receiver_port file.txt
    print("Setup sender")
    if len(sys.argv) < n_expected_args:
        print("Usage: python receiver.py receiver_port file.txt")
    else:

        receiver_port, file_name = sys.argv[1:]
        receiver = Receiver()
