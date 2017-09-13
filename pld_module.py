#!/usr/bin/python3
# Emulate packet loss & delay here
import random as r


class PacketThrottler:
    def __init__(self, seed_val, pdrop):
        r.seed(seed_val)
        self.pdrop = pdrop

    def should_transmit_packet(self):
        return True if r.random() > self.pdrop else False

    def get_random_init_seq_num(self):
        """
        Gets a random int less than 1000
        """
        return r.randint(0, 1000)
