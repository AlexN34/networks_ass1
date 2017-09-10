#!/usr/bin/python3
import sys
import os
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
    # timer expiry
    # on send
    # make a timer, start()

    # packet failed to be received
    # stp_retransmit

    # packet received:
    # self.timer.cancel()

    def __init__(self, receiver_host_ip, receiver_port, timeout_length):
        self.receiver_host_ip, self.receiver_port = receiver_host_ip, receiver_port
        self.packet_buffer = {}

    # specify timeout_length. if this fails then it calls stp.retransmit(seq_num)
    # TODO figure out timeout; get from packet buffer?
    # self.sender_timer = Timer(timeout_length, self.stp_retransmit, args=[seq_num])

    def set_timer(self):
        print("dummy")

    def open_connection(self):
        print("dummy")
        try:
            self.connection_socket = socket.socket(socket.AF_INET,
                                                   socket.SOCK_DGRAM)
        except socket.error:
            print("Failed to create socket")
            sys.exit()

    def close_connection(self):
        self.connection_socket.close()

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


n_expected_args = 9
if __name__ == "__main__":
    # python sender.py receiver_host_ip receiver_port file.txt MWS MSS timeout pdrop seed
    # MWS: max window size in bytes
    # MSS: max segmet size (max data in bytes carried in each STP_packet)
    # pdrop: probability to drop 0-1, seed: seed for rgeerator
    # use the same socket for send packets/receiver ack - acks bypass pld
    # v1 - alternating bit using seq 0-1 only
    print("Setup sender")
    if len(sys.argv) < n_expected_args:
        print(
            "Usage: python sender.py receiver_host_ip receiver_port file.txt MWS MSS timeout pdrop seed"
        )
    else:

        receiver_host_ip, receiver_port, file_name, MWS, MSS, timeout, pdrop, seed = sys.argv[
            1:]
        sender = Sender()
        data = ""
        sender.open_connection()
        stp_packet = stp_packet.STPPacket(data, 0, 0, syn=True)
        socket.socket()
