#!/usr/bin/python3
import sys
from stp_packet import STPPacket
import pickle
import socket
import time
import itertools
from threading import Timer

# self.sender_timer = Timer(
#     timeout_length, self.stp_retransmit, args=[seq_num])
# self.sender_timer.start()

# def stp_retransmit(self, seq_num):
#     self.stp_transmit(self.packet_buffer[seq_num])
#     # reset timer

# def stp_receive(self, seq_num):
#     self.sender_timer.cancel()


class Sender:
    # timer expiry
    # on send
    # make a timer, start()

    # packet failed to be received
    # stp_retransmit

    # packet received:
    # self.timer.cancel()
    # TODO schedule send packet phase -> receive ack phase -> etc state machine

    def __init__(self, receiver_host_ip, receiver_port, mss, timeout_length):
        self.receiver_host_ip = receiver_host_ip
        self.receiver_port = receiver_port
        self.timeout_length = timeout_length
        self.mss = mss
        self.buffer_size = 4096
        self.connection_socket = self.open_connection()
        self.packet_buffer = {}
        self.log_name = "Sender_log.txt"
        open(self.log_name, 'w').close()  # clear old log
        # Base asst, no packet delay
        self.run_stats = {
            "bytes_sent": 0,
            "segments_sent": 0,
            "duplicates_sent": 0,
            "packets_dropped": 0,
            "duplicates_ack": 0
        }
        self.run_stats_msgs = {
            "bytes_sent":
            'Amount of (original) Data Transferred (in bytes): {}\n',
            "segments_sent":
            'Number of (original) Data Segments Sent: {}\n',
            "duplicates_sent":
            'Number of Duplicate Acknowledgements received: {}\n',
            "packets_dropped":
            'Number of Dropped packets: {}\n',
            "duplicates_ack":
            'Number of Duplicate Acknowledgements received: {}\n'
        }
        self.start_time = time.time()  # TODO funny time values calc'd.. check
        self.seq_gen = itertools.cycle([0, 1])  # rdt3.0 uses 0-1 cycling
        self.next_seq_num = 0
        self.send_base = self.next_seq_num

    # specify timeout_length. if this fails then calls stp.retransmit(seq_num)
    # TODO figure out timeout; get from packet buffer?

    # def set_timer(self):
    #     print("dummy")

    def open_connection(self):
        print("dummy")
        try:
            connection_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
            return connection_socket
        except socket.error:
            print("Failed to create socket")
            sys.exit()

    def close_connection(self):
        """
        sender teardown operations: close socket, make final log
        """
        self.connection_socket.close()
        sender.close_log()

    def send_packet(self, stp_packet):
        # index by sequence number
        self.packet_buffer[stp_packet.seq_num] = stp_packet
        self.connection_socket.sendto(
            pickle.dumps(stp_packet), (self.receiver_host_ip,
                                       self.receiver_port))
        min_not_acked_seq_num = min(self.packet_buffer.keys())
        self.sender_timer = Timer(
            self.timeout_length,
            self.retransmit_packet,
            args=[min_not_acked_seq_num])
        # start the timer
        self.sender_timer.start()
        self.update_log('snd', 'D', stp_packet)

    def retransmit_packet(self, seq_num):
        retransmit_packet = self.packet_buffer[seq_num]
        self.send_packet(retransmit_packet)

    def receive_packet(self):
        """
        Returns boolean signifying whether received packet is
        the next expected one
        """
        data, addr = self.connection_socket.recvfrom(self.buffer_size)
        stp_packet = pickle.loads(data)  # data is property of stp_packet
        print("Sender Received packet. addr: {}".format(addr))
        stp_packet.print_properties()
        received_ack = stp_packet.ack_num
        if stp_packet.ack is True:
            if received_ack >= self.send_base:
                self.update_log('rcv', 'A', stp_packet)
                self.process_ack(stp_packet.ack_num)
                self.send_base = received_ack
                return True
        return False

    # current waiting ack received; cancel timer
    def process_ack(self, seq_num):
        del (self.packet_buffer[seq_num])
        self.sender_timer.cancel()
        # if unacknowledged segments exist, start again?

    def process_file(self, file_path):
        # file.txt is closed after open
        with open(file_path, 'rb') as handle:
            self.file_bytes = list(handle.read())

    def get_packet_data_size(self):
        # TODO do min(mss, mws) - sizeof empty packet object
        return self.mss

    def get_packet_data(self, num_bytes):
        # get bytes, remove from bytes left to send
        packet_bytes = self.file_bytes[:num_bytes]
        self.file_bytes = self.file_bytes[num_bytes:len(self.file_bytes)]
        return packet_bytes

    def form_stp_packet(self):
        """
        creates a new unique stp packet for sending and saves state with sender
        """
        data_size = self.get_packet_data_size()
        packet_data = self.get_packet_data(data_size)
        # does sender need to include an ack_num? unidirectional? check..
        new_packet = STPPacket(
            bytes(packet_data), self.next_seq_num, self.next_seq_num)
        self.next_seq_num = self.next_seq_num + len(bytes(packet_data))

        return new_packet

    def max_expected_ack(self):
        return max(self.packet_buffer.keys())  # keys are all sequence numbers

    def update_log(self, packet_action, packet_type, stp_packet):
        if packet_action == "snd":
            self.run_stats["bytes_sent"] += len(stp_packet.data)
            # TODO Check if duplicate packet, incr counter sent
            self.run_stats["segments_sent"] += 1
        time_since_excution = (time.time() - self.start_time) * 1000  # ms
        with open(self.log_name, 'a') as handle:
            handle.write('{} {} {} {} {} {}\n'.format(
                packet_action, time_since_excution, packet_type,
                stp_packet.seq_num, len(stp_packet.data), stp_packet.ack_num))

    def close_log(self):
        with open(self.log_name, 'a') as handle:
            for key in self.run_stats_msgs:
                handle.write(self.run_stats_msgs[key]
                             .format(self.run_stats[key]))


if __name__ == "__main__":
    # python sender.py receiver_host_ip receiver_port file.txt MWS MSS
    # MWS: max window size in bytes
    # MSS: max segmet size (max data in bytes carried in each STP_packet)
    # pdrop: probability to drop 0-1, seed: seed for rgeerator
    # use the same socket for send packets/receiver ack - acks bypass pld
    # v1 - rdt3.0 alternating bit using seq 0-1 only
    n_expected_args = 9
    print("Setup sender")
    if len(sys.argv) < n_expected_args:
        print(
            "Usage: python sender.py receiver_host_ip receiver_port file.txt \
                MWS MSS timeout pdrop seed")
    else:

        receiver_host_ip, receiver_port, file_path, \
                mws, mss, timeout, pdrop, seed = sys.argv[1:]
        sender = Sender(receiver_host_ip, int(receiver_port), int(mss),
                        timeout)
        sender.process_file(file_path)
        print("Sender setup, connection opened details: {}".format(
            sender.connection_socket.getsockname()))
        # Operate webserver whilst there is stuff left to transfer
        while len(sender.file_bytes) > 0:
            cur_packet = sender.form_stp_packet()
            sender.send_packet(cur_packet)
            # sent packet, change into ack wait mode
            while not sender.receive_packet():
                pass

            print("Just sent packet: {}".format(cur_packet))
        print("All packets sent - no more packet sending, close connection")
        sender.send_packet(STPPacket('~', 0, 0))
        sender.close_connection()

        # TODO questions:
        # 1. structure 2. pick seq # starting, pick ack from sender?
        # does connection die after JUST transfer the file? when to close?
        # MSS / MWS determine how big chunks to break file into?
        # ^ calculate size of total packet, then just put data in to fill?
        # sender should send acks to say it's received
        # pick random for start
