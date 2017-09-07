#!/usr/bin/python3
import stp_packet
import pickle
import socket
from timer import Timer


class Sender:
    # Sender -> seq = 10 ->
    # sender also needs sequence number
    # Sender
    # 1: sq 1 get ack 11 -> send which packet to repeat ( if needed)
    # 2: seq 11
    # 3 : seq 21
    # store packets? use a dict
    # dict = {}
    # dict[seq_number] = stp_packet

    # you need to create this.
    # a lot more complicated, but just follow the assignment spec
    # you can do go-back-N, selective repeat, whatever works
    # also needs sequence number
    #timer expiry
    #on send
    #make a timer, start()

    #packet failed to be received
    #stp_retransmit

    #packet received:
    #self.timer.cancel()

    connection_socket = socket.create_connection(socket.SOCK_DGRAM)
    client_ip = 'localhost'
    client_port = 5000
    self.packet_buffer = {}
    # specify timeout_length. if this fails then it calls stp.retransmit(seq_num)
    sender_timer = Timer(timeout_length, self.stp_retransmit, args=[seq_num])

    def set_timer(self):
        print("dummy")

    def open_connection(self):
        print("dummy")

    def close_connection(self):
        print("dummy")

    def send_packet(self, stp_packet):
        #stp_packet = STPPacket(data, ..)
        self.connection_socket.sendto(
            pickle.dumps(stp_packet), (self.client_ip, self.client_port))
        self.sender_timer = Timer(
            timeout_length, self.stp_retransmit, args=[seq_num])
        self.sender_timer.start()

    def stp_retransmit(self, seq_num):
        self.stp_transmit(self.packet_buffer[seq_num])
        # reset timer
    def stp_receive(self, seq_num):
        self.sender_timer.cancel()


if __name__ == "__main__":
    # python sender.py receiver_host_ip receiver_port file.txt MWS MSS timeout pdrop seed
    print("Setup sender")
