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

    # use the same socket for send packets/receiver ack - acks bypass pld
    # output to Seder_log.txt for each segmet sent ad received
    # log format: <snd/rcv/drop> <time> <type of packet> <seq-number> <number-of- bytes> <ack-number>
    # where <type of packet> could be S (SYN), A (ACK), F (FIN) and D (Data)
    # Once the entire file has been transmitted reliably the Sender should initiate the connection closure process by sending a FIN segment
    # The Sender should also print the following statistics at the end of the log file (i.e. Sender_log.txt):
    # • Amount of (original) Data Transferred (in bytes)
    # • Number of Data Segments Sent (excluding retransmissions)
    # • Number of (all) Packets Dropped (by the PLD module)
    # • Number of (all) Packets Delayed (for the extended assignment only)
    # • Number of Retransmitted Segments
    # • Number of Duplicate Acknowledgements received

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


n_expected_args = 9
if __name__ == "__main__":
    # python sender.py receiver_host_ip receiver_port file.txt MWS MSS timeout pdrop seed
    # MWS: max window size in bytes
    # MSS: max segmet size (max data in bytes carried in each STP_packet)
    # pdrop: probability to drop 0-1, seed: seed for rgeerator
    print("Setup sender")
    if len(sys.argv) < n_expected_args:
        print(
            "Usage: python sender.py receiver_host_ip receiver_port file.txt MWS MSS timeout pdrop seed"
        )
    else:

        receiver_host_ip, receiver_port, file_name, MWS, MSS, timeout, pdrop, seed = sys.argv[
            1:]
