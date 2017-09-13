#!/usr/bin/python3
from stp_packet import STPPacket
import pickle
import socket
import sys
import time
from random import randint, seed

# verbose_flag = True

verbose_flag = False


class Receiver:
    def __init__(self, receiver_port, file_path):
        # TODO make file to write into when appropriate
        self.file_name = file_name
        # TODO check hostname - local?
        self.connection_socket = self.open_connection("", receiver_port)
        self.received_bytes = b''
        self.buffer_size = 4096
        self.log_name = "Receiver_log.txt"
        open(self.log_name, 'w').close()  # clear old log
        self.run_stats = {
            "bytes_received": 0,
            "segments_received": 0,
            "duplicates_received": 0
        }
        self.run_stats_msgs = {
            "bytes_received":
            'Amount of (original) Data Received (in bytes): {}\n',
            "segments_received":
            'Number of (original) Data Segments received: {}\n',
            "duplicates_received":
            'Number of Duplicate Segments received: {}\n'
        }
        self.packet_buffer = {}
        self.start_time = time.time()  # start tracking time on make
        # set up in syn/synack/ack?
        self.next_seq_num = None  # sender next expected seq num; used as ack_num
        self.receiver_seq_num = None  #
        self.init_seq_num = randint(
            0, 1000)  # pick random starting sequence number

    def write_file(self, file_path):
        with open(file_path, 'wb') as handle:
            handle.write(self.received_bytes)

    def update_packet_buffer(self):
        while self.next_seq_num in list(self.packet_buffer.keys()):
            cur_packet = self.packet_buffer[self.next_seq_num]
            self.run_stats["segments_received"] += 1
            self.run_stats["bytes_received"] += len(cur_packet.data)
            self.received_bytes += cur_packet.data
            del (self.packet_buffer[self.next_seq_num])
            self.next_seq_num += len(cur_packet.data)

    def receive_packet(self):
        """
        return value indicating whether packet modified
        """
        data, addr = self.connection_socket.recvfrom(self.buffer_size)
        stp_packet = pickle.loads(data)  # data is property of stp_packet
        self.sender_address = addr
        if verbose_flag:
            print("Received packet. addr: {}".format(addr))
            stp_packet.print_properties()
        # buffer if new - could be out of order, though
        if stp_packet.seq_num not in self.packet_buffer.keys():
            self.packet_buffer[stp_packet.seq_num] = stp_packet
            # TODO Check if duplicate packet, incr counter received instead of below

        # check if out of order - if in order, update expected seq
        if verbose_flag:
            print(
                "about to decide whetehr to update packet buffer. packet seq num is: {}, next seq num is: {}".
                format(stp_packet.seq_num, self.next_seq_num))

        packet_type = self.get_packet_type(stp_packet)
        if stp_packet.seq_num == self.next_seq_num:
            # move window up; everything past this has been acknowledged
            # move as many as there are in order
            # import pdb
            # pdb.set_trace()
            if verbose_flag:
                print("decided - updating packet buffer")
            self.update_packet_buffer()
            if packet_type == 'D':
                self.receiver_seq_num = stp_packet.ack_num
            elif packet_type == 'F':
                if verbose_flag:
                    print("About to attempt close receiver stp")
                self.update_log('rcv',
                                self.get_packet_type(stp_packet), stp_packet)
                self.close_stp()
        elif stp_packet.seq_num < self.next_seq_num or stp_packet.seq_num in self.packet_buffer.keys(
        ):
            self.run_stats["duplicates_received"] += 1

        if packet_type != 'F':
            self.update_log('rcv', self.get_packet_type(stp_packet),
                            stp_packet)
        # previous if updates seq/ack variables so next ack is always right
        # received something out of order, keep asking for the right one
        if self.stp_flag:
            if verbose_flag:
                print("decided - not update packet buffer, ack")
            self.send_ack(self.receiver_seq_num, self.next_seq_num)
        if verbose_flag:
            print("about to leave receive_packet")

    def receive_syn(self):
        data, addr = self.connection_socket.recvfrom(self.buffer_size)
        stp_packet = pickle.loads(data)  # data is property of stp_packet
        self.sender_address = addr
        if verbose_flag:
            print("Received syn packet. addr: {}".format(addr))

        packet_type = self.get_packet_type(stp_packet)
        self.update_log('rcv', packet_type, stp_packet)
        if packet_type == 'S':
            self.next_seq_num = stp_packet.seq_num  # used in ack_num
            self.receiver_seq_num = self.init_seq_num  # used in pckt seq_num
            return True
        return False

    def send_synack(self):
        synack_packet = STPPacket(
            b'',
            self.receiver_seq_num,
            self.next_seq_num + 1,
            syn=True,
            ack=True)
        self.connection_socket.sendto(
            pickle.dumps(synack_packet), self.sender_address)
        self.update_log('snd',
                        self.get_packet_type(synack_packet), synack_packet)

    def send_fin_ack(self):
        fin_packet = STPPacket(
            b'', self.receiver_seq_num, self.next_seq_num, ack=True, fin=True)
        self.update_log('snd', self.get_packet_type(fin_packet), fin_packet)
        self.connection_socket.sendto(
            pickle.dumps(fin_packet), self.sender_address)

    def receive_sender_ack(self):
        data, addr = self.connection_socket.recvfrom(self.buffer_size)
        stp_packet = pickle.loads(data)  # data is property of stp_packet
        self.sender_address = addr

        if verbose_flag:
            print("Received sender ack packet. addr: {}".format(addr))
            stp_packet.print_properties()

        packet_type = self.get_packet_type(stp_packet)
        if packet_type == 'A':
            if stp_packet.ack_num == self.init_seq_num + 1 \
                and stp_packet.seq_num == self.next_seq_num + 1:
                # SYN acknolwedgement
                self.next_seq_num = stp_packet.seq_num
            # else:
            # FIN acknowledgement
            #     self.close_connection()
            self.update_log('rcv', self.get_packet_type(stp_packet),
                            stp_packet)
            return True
        return False

    def send_ack(self, seq_num, ack_num):
        # Data is blank - ack
        # seq num is next byte needed
        # we leave the receiver's sequence number as is as it is not transmitting
        # any data at the moment
        ack_packet = STPPacket(b'', seq_num, ack_num, ack=True)
        self.connection_socket.sendto(
            pickle.dumps(ack_packet), self.sender_address)
        self.update_log('snd', self.get_packet_type(ack_packet), ack_packet)

    def open_connection(self, host, receiver_port):
        try:
            connection_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
            connection_socket.bind((host, receiver_port))
            return connection_socket
        except socket.error:
            print("Failed to create socket")
            sys.exit()

    def close_connection(self):
        self.run_stats[
            "segments_received"] -= 1  # off by 1 somewhere ... need to debug
        self.write_file(file_name)
        self.close_log()
        self.connection_socket.close()

    def update_log(self, packet_action, packet_type, stp_packet):
        # if packet_action == "rcv":
        #     self.run_stats["bytes_received"] += len(stp_packet.data)
        #     # TODO Check if duplicate packet, incr counter received instead of below
        #     self.run_stats["segments_received"] += 1
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
        # LISTEN state
        while not self.receive_syn():
            pass
        # SYN_RCVD state
        self.send_synack()
        while not self.receive_sender_ack():
            pass  # no need to resend synack, should be no pld
        # ESTABLISHED
        self.stp_flag = True

    def close_stp(self):
        """
        called when we detect sender wants to close - start in CLOSE_WAIT state
        """
        # CLOSE_WAIT
        self.send_fin_ack()
        # LAST_ACK
        while not self.receive_sender_ack():
            pass
        self.stp_flag = False


n_expected_args = 3
if __name__ == "__main__":
    # do setup when run TODO make new log file?
    # python receiver.py receiver_port file.txt
    if len(sys.argv) < n_expected_args:
        print("Usage: python receiver.py receiver_port file.txt")
    else:
        seed(1)  # seed used in random int
        receiver_port, file_name = sys.argv[1:]
        receiver = Receiver(int(receiver_port), file_name)
        if verbose_flag:
            print("Receiver setup, waiting on port: {}".format(receiver_port))
        # waits for sender to intiate stp
        receiver.initiate_stp()
        while receiver.stp_flag:
            receiver.receive_packet()

        receiver.close_connection()
