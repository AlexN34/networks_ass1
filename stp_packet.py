#!/usr/bin/python3
import stp_packet_header as STPHeader


class STPPacket:
    def __init__(self,
                 data,
                 seq_num,
                 ack_num,
                 ack=False,
                 syn=False,
                 fin=False,
                 mss):
        self.data = data
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.ack = ack
        self.syn = syn
        self.fin = fin
        self.mss = mss  # max segment size; data must not exceed this TODO check if req'd in this, perhaps default data to none - ack packets have no data
