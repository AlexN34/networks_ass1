#!/usr/bin/python3


# Header file stuff goes here
# TCP structure: Source port #
# Header len?
# Dest port #
# Seq #
# Ack #
# ACK SYN FIN MSS?
# Data
class STPHeader:
    def __init__(self, src_port, dest_port, seq, ack, fin, mss):
        self.src_port = src_port
        self.dest_port = dest_port
        self.seq = seq
        self.ack = ack
        self.fin = fin
        self.mss = mss

    def get_src_port(self):
        return self.src_port

    def set_src_port(self, src_port):
        self.src_port = src_port

    def get_dest_port(self):
        return self.dest_port

    def set_dest_port(self, dest_port):
        self.dest_port = dest_port

    def has_syn_flag(self):
        return self.syn

    def set_syn_flag(self, syn):
        self.syn = syn

    def has_fin_flag(self):
        return self.fin

    def set_fin_flag(self, fin):
        self.fin = fin

    def get_ack(self):
        return self.ack

    def set_ack(self, ack):
        self.ack = ack

    def get_seq(self):
        return self.seq

    def set_seq(self, seq):
        self.seq = seq

    def get_mss(self):
        return self.mss

    def set_mss(self, mss):
        self.mss = mss
