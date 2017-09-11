#!/usr/bin/python3
import sys
from stp_packet import STPPacket
import pickle
import socket
import time
import itertools
from threading import Timer
from random import randint

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
    # TODO window size - method to look inside packet_buffer and see active bytes

    def __init__(self, receiver_host_ip, receiver_port, mws, mss,
                 timeout_length):
        self.receiver_host_ip = receiver_host_ip
        self.receiver_port = receiver_port
        self.timeout_length = timeout_length
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
            'Amount of (original) Data Transferred (in bytes) {}\n',
            "segments_sent":
            'Number of  Data Segments Sent (excluding retransmissions) {}\n',
            "packets_dropped":
            'Number of (all) Packets Dropped {}\n',
            "duplicates_sent":
            'Number of Retransmitted Segments {}\n',
            "duplicates_ack":
            'Number of Duplicate Acknowledgements received {}\n'
        }
        self.start_time = time.time()  # TODO funny time values calc'd.. check
        self.init_seq_num = randint(
            0, 1000)  # pick random starting sequence number
        self.next_seq_num = self.init_seq_num
        self.receiver_seq_num = randint(
            0, 1000)  # pick random starting sequence number
        self.send_base = self.next_seq_num
        self.mss = mss
        self.mws = mws
        self.prev_duplicates_received = 0

    # specify timeout_length. if this fails then calls stp.retransmit(seq_num)
    # TODO figure out timeout; get from packet buffer?

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
        # index by sequence number + len(data) (for access on ack)
        self.packet_buffer[stp_packet.seq_num] = stp_packet
        self.connection_socket.sendto(
            pickle.dumps(stp_packet), (self.receiver_host_ip,
                                       self.receiver_port))
        self.set_timer()
        # start the timer
        if timer_flag:
            print("starting timer")
            self.sender_timer.start()
        self.update_log('snd', 'D', stp_packet)

    def retransmit_packet(self, seq_num):
        print("timer expired: about to retransmit seq num: {}".format(seq_num))
        retransmit_packet = self.packet_buffer[seq_num]
        self.send_packet(retransmit_packet)
        self.run_stats["duplicates_sent"] += 1

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
            if received_ack > self.send_base:
                self.update_log('rcv', 'A', stp_packet)
                # ack_num will be 1 more than last acked byte
                self.process_ack(self.send_base)
                self.send_base = received_ack
                if len(self.packet_buffer) > 0:
                    print("""received packet with ack_num: {}
                             there are still unacknowledged packets,
                             resetting timer
                          """.format(received_ack))
                    self.set_timer()
                    if timer_flag:
                        self.sender_timer.start()
                return True
            else:
                self.prev_duplicates_received += 1
                self.run_stats["duplicates_ack"] += 1
                if self.prev_duplicates_received == 3:
                    self.prev_duplicates_received = 0  # reset
                    self.retransmit_packet(self.send_base)
        return False

    # current waiting ack received; cancel timer
    def process_ack(self, seq_num):
        del (self.packet_buffer[seq_num])
        if timer_flag:
            self.sender_timer.cancel()
        print("just stopped timer")
        # if unacknowledged segments exist, start again?

    def process_file(self, file_path):
        # file.txt is closed after open
        with open(file_path, 'rb') as handle:
            self.file_bytes = list(handle.read())

    def get_packet_data_size(self):
        # TODO do min(mss, mws) - sizeof empty packet object
        # n segments = int(len(self.file_bytes) / self.mss)
        # if there isn't enough space
        if self.mss < self.mws:
            available_window_bytes = self.mws - self.get_cur_window_size()
            if available_window_bytes > 0:
                if available_window_bytes >= self.mss:
                    return self.mss  # if there's space, send max segment
                else:
                    return available_window_bytes  # otherwise send what's left
            else:
                raise ValueError(
                    'Trying to get packet data size to make new packet with no window space'
                )
        else:
            return mws  # if window is smaller, just saturate the window

    def get_packet_data(self, num_bytes):
        # get bytes, remove from bytes left to send
        packet_bytes = self.file_bytes[:num_bytes]
        self.file_bytes = self.file_bytes[num_bytes:len(self.file_bytes)]
        return packet_bytes

    def get_cur_window_size(self):
        print("window size is: {}".format(self.next_seq_num - self.send_base))
        return self.next_seq_num - self.send_base  # (-1's cancel)

    def form_stp_packet(self):
        """
        creates a new unique stp packet for sending and saves state with sender
        """
        packet_data_size = self.get_packet_data_size()
        packet_data = self.get_packet_data(
            packet_data_size)  # use constant in init
        # does sender need to include an ack_num? unidirectional? check..
        new_packet = STPPacket(
            bytes(packet_data), self.next_seq_num, self.receiver_seq_num)
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

    def set_timer(self):
        min_not_acked_seq_num = min(self.packet_buffer.keys())
        if timer_flag:
            self.sender_timer = Timer(
                self.timeout_length,
                self.retransmit_packet,
                args=[min_not_acked_seq_num])


if __name__ == "__main__":
    # python sender.py receiver_host_ip receiver_port file.txt MWS MSS
    # MWS: max window size in bytes
    # MSS: max segmet size (max data in bytes carried in each STP_packet)
    # pdrop: probability to drop 0-1, seed: seed for rgeerator
    # use the same socket for send packets/receiver ack - acks bypass pld
    # v1 - rdt3.0 alternating bit using seq 0-1 only
    n_expected_args = 9
    timer_flag = False
    print("Setup sender")
    if len(sys.argv) < n_expected_args:
        print(
            "Usage: python sender.py receiver_host_ip receiver_port file.txt \
                MWS MSS timeout pdrop seed")
    else:

        receiver_host_ip, receiver_port, file_path, \
                mws, mss, timeout, pdrop, seed = sys.argv[1:]
        sender = Sender(receiver_host_ip,
                        int(receiver_port),
                        int(mws), int(mss),
                        int(timeout) / 1000)  # timeout input convert ms to s
        sender.process_file(file_path)
        print("Sender setup, connection opened details: {}".format(
            sender.connection_socket.getsockname()))
        # Operate webserver whilst there is stuff left to transfer
        while len(sender.file_bytes) > 0:
            while int(mws) - sender.get_cur_window_size() > 0 and len(
                    sender.file_bytes) > 0:  # send until window fills

                cur_packet = sender.form_stp_packet()
                sender.send_packet(cur_packet)
            # sent packet, change into ack wait mode
            while not sender.receive_packet():
                pass

            print("Just sent packet: {}".format(cur_packet))
        print("All packets sent - no more packet sending, close connection")
        # workaround, replace with FIN/SYN cycle
        sender.send_packet(STPPacket('~', 0, 0))
        if timer_flag:
            sender.sender_timer.cancel()  # finish, stop timing
        sender.close_connection()

        # TODO questions:
        # 1. structure 2. pick seq # starting, pick ack from sender?
        # does connection die after JUST transfer the file? when to close?
        # MSS / MWS determine how big chunks to break file into?
        # ^ calculate size of total packet, then just put data in to fill?
        # sender should send acks to say it's received
        # pick random for start
