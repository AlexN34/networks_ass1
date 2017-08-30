#!/usr/bin/python3
import stp_packet_header as STPHeader


class STPPacket:
    def __init__(self, data):
        self.header = STPHeader.STPHeader()
        self.data = data
