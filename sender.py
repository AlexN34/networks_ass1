#!/usr/bin/python3
import sys
from stp_packet import STPPacket
import pickle
import socket
import time
import itertools
from threading import Timer
import random


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
        self.init_seq_num = random.randint(
            0, 1000)  # pick random starting sequence number
        self.next_seq_num = self.init_seq_num
        self.receiver_seq_num = None  # Set by synack packet
        self.send_base = self.next_seq_num
        self.mss = mss
        self.mws = mws
        self.prev_duplicates_received = 0
        self.sender_timer = None

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
        print("Inside close connection, about to shut down")
        if timer_flag:
            self.sender_timer.cancel()  # about to finish, stop timer
        self.connection_socket.close()
        self.close_log()

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
        send_type = self.get_packet_type(stp_packet)
        self.update_log('snd', send_type, stp_packet)
        self.next_seq_num += len(stp_packet.data)

    def retransmit_packet(self, seq_num):
        print("timer expired: about to retransmit seq num: {}".format(seq_num))
        retransmit_packet = self.packet_buffer[seq_num]
        self.send_packet(retransmit_packet)
        self.run_stats["duplicates_sent"] += 1

    def receive_synack(self):
        data, addr = self.connection_socket.recvfrom(self.buffer_size)
        stp_packet = pickle.loads(data)  # data is property of stp_packet
        print("Sender Received packet. addr: {}".format(addr))
        stp_packet.print_properties()
        if stp_packet.syn and stp_packet.ack and stp_packet.ack_num > self.send_base:
            self.receiver_seq_num = stp_packet.seq_num
            self.update_log('rcv', self.get_packet_type(stp_packet),
                            stp_packet)
            # ack_num will be 1 more than last acked byte
            self.process_ack(self.send_base)
            self.send_base = stp_packet.ack_num
            return True
        return False

    def receive_fin_ack(self):
        data, addr = self.connection_socket.recvfrom(self.buffer_size)
        stp_packet = pickle.loads(data)  # data is property of stp_packet
        if stp_packet.ack and stp_packet.fin:
            self.process_ack(self.next_seq_num)
            self.update_log('rcv', self.get_packet_type(stp_packet),
                            stp_packet)
            return True
        return False

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
        if stp_packet.ack:  # we received an ack
            if received_ack > self.send_base:
                self.update_log('rcv',
                                self.get_packet_type(stp_packet), stp_packet)
                # ack_num will be 1 more than last acked byte
                self.process_ack(self.send_base)
                self.send_base = received_ack
                if len(self.packet_buffer) > 0:
                    print("""received packet with ack_num: {}
                            there are still unacknowledged packets: {},
                            resetting timer
                        """.format(received_ack, self.packet_buffer.keys()))
                    self.set_timer()
                    if timer_flag:
                        self.sender_timer.start()
                return True
            else:
                print("triggered duplicates!")
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

        return new_packet

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
        print('About to close off log')
        with open(self.log_name, 'a') as handle:
            for key in self.run_stats_msgs:
                handle.write(self.run_stats_msgs[key]
                             .format(self.run_stats[key]))

    def set_timer(self):
        if self.sender_timer is not None:
            self.sender_timer.cancel()
        min_not_acked_seq_num = min(self.packet_buffer.keys())
        send_type = self.get_packet_type(
            self.packet_buffer[min_not_acked_seq_num])
        if timer_flag:
            self.sender_timer = Timer(
                self.timeout_length,
                self.retransmit_packet,
                args=[min_not_acked_seq_num])

    def set_close_timer(self, timeout_length):
        print("About to set close connection timer of length: {}".format(
            timeout_length))
        if self.sender_timer is not None:
            self.sender_timer.cancel()
        if timer_flag:
            self.sender_timer = Timer(timeout_length, self.close_connection)
            self.sender_timer.start()

    def get_packet_type(self, stp_packet):

        if len(stp_packet.data) > 0:
            return 'D'
        else:
            result = ''
            if stp_packet.fin:
                result += 'F'
            elif stp_packet.syn:
                result += 'S'
            if stp_packet.ack:
                result += 'A'
            return result

    def initiate_stp(self):
        init_packet = STPPacket('', self.init_seq_num, None, syn=True)
        # send SYN packet; timer will handle retransmits
        self.send_packet(init_packet)
        self.next_seq_num += 1  # increment next packet number even though 0 data sent
        # SYN_SENT beyond this point
        while not self.receive_synack():  # wait for SYNACK packet
            pass
        self.receiver_seq_num += 1  # synack processed, first packet sent will do acknowledging
        # send ACK to SYNACK with no data; timer handles retransmit
        self.send_packet(
            STPPacket('', self.next_seq_num, self.receiver_seq_num, ack=True))
        # ESTABLISHED beyond this point

    def close_stp(self):
        fin_packet = STPPacket(
            '', self.next_seq_num, self.receiver_seq_num, fin=True)
        # send SYN packet; timer will handle retransmits
        print("About to send fin packet")
        self.send_packet(fin_packet)
        # FIN_WAIT_1 beyond this point
        # FIN_WAIT_2 beyond this point
        print("About to wait on fin ack packet")
        while not self.receive_fin_ack():  # wait for SYNACK packet
            pass
        print("About to ack receiver finack packet")
        ack_packet = STPPacket(
            '', self.next_seq_num, self.receiver_seq_num, ack=True)
        self.send_packet(ack_packet)
        # TIME_WAIT beyond tthis point
        # override default timer; close down after 2 * input timeout
        self.set_close_timer(self.timeout_length * 2)


if __name__ == "__main__":
    # TODO event loop question... setting varialbes in init method instead of after synack ok?
    # TODO textbook says sender ack carries payload, spec example does not. which one?
    # TODO sender ack permanently increases receiver's seq number?
    # TODO deallocation on finish?
    # python sender.py receiver_host_ip receiver_port file.txt MWS MSS
    # MWS: max window size in bytes
    # MSS: max segmet size (max data in bytes carried in each STP_packet)
    # pdrop: probability to drop 0-1, seed: seed for rgeerator
    # use the same socket for send packets/receiver ack - acks bypass pld
    # TODO synack stuff
    # TODO close connection
    n_expected_args = 9
    timer_flag = True
    print("Setup sender")
    if len(sys.argv) < n_expected_args:
        print(
            """Usage: python sender.py receiver_host_ip receiver_port file.txt
                MWS MSS timeout pdrop seed""")
    else:

        receiver_host_ip, receiver_port, file_path, \
                mws, mss, timeout, pdrop, seed = sys.argv[1:]
        random.seed(int(seed))
        sender = Sender(receiver_host_ip,
                        int(receiver_port),
                        int(mws), int(mss),
                        int(timeout) / 1000)  # timeout input convert ms to s
        sender.process_file(file_path)
        print("Sender setup, connection opened details: {}".format(
            sender.connection_socket.getsockname()))
        # Operate webserver whilst there is stuff left to transfer
        # OR still waiting for acks
        # loop inside intiate until success
        sender.initiate_stp()
        while len(sender.file_bytes) > 0 or len(
                sender.packet_buffer.keys()) > 0:
            while int(mws) - sender.get_cur_window_size() > 0 and len(
                    sender.file_bytes) > 0:  # send until window fills

                cur_packet = sender.form_stp_packet()
                sender.send_packet(cur_packet)
            # sent packet, change into ack wait mode
            while not sender.receive_packet():
                pass

            print("Just sent packet: {}".format(cur_packet))
        print("All packets sent - no more packet sending, close connection")
        sender.close_stp()
        # workaround, replace with FIN/SYN cycle
        # sender.send_packet(STPPacket('~', 0, 0))
        # if timer_flag:
        #     sender.sender_timer.cancel()  # finish, stop timing
        # sender.close_connection()

        # TODO questions:
        # 1. structure 2. pick seq # starting, pick ack from sender?
        # does connection die after JUST transfer the file? when to close?
        # MSS / MWS determine how big chunks to break file into?
        # ^ calculate size of total packet, then just put data in to fill?
        # sender should send acks to say it's received
        # pick random for start
