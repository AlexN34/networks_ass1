#!/usr/bin/python3
from pprint import pprint
import re


class STPPacket:
    def __init__(
            self,
            data,
            seq_num,
            ack_num,
            ack=False,
            syn=False,
            fin=False, ):
        self.data = data
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.ack = ack
        self.syn = syn
        self.fin = fin

    def print_properties(self):
        for packet_attr in dir(self):
            if re.match('^__.*__$', packet_attr):
                continue
            else:
                prop = getattr(self, packet_attr)
                if not callable(prop):  # exclude methods
                    pprint("{}: {}".format(packet_attr, prop))
                    if packet_attr == "data":
                        pprint("type of data: {}".format(type(prop)))
