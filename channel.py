import csv
import random

from waa import myglobal

class Channels():
    db=[]

    def get_one_unlucky_node_id(self):
        mylist=self.get_unlucky_nodes_list()
        if len(mylist)==0:
            return myglobal.DEFAULT_UNLUCKY_NODE_ID
        else:
            return random.choice(mylist)

    def get_unlucky_nodes_list(self):
        mylist=[]
        for ch in self.db:
            ret=ch.get_unlucky_list()
            if ret is not None:
                mylist.extend(ret)
        return mylist

    def get_common_bitrate(self):
        if len(self.db)<1:
            print('ERROR! Cannot find channels')
            return 0
        else:
            common_bitrate=self.db[0].bitrate
        for ch in self.db:
            if ch.bitrate!=common_bitrate:
                print('ERROR! Variable cycles!')
                return 0
        return common_bitrate


    def add_new(self,channel):
        self.db.append(channel)

    def get_channel_from_id(self,id):
        for channel in self.db:
            if channel.id==id:
                return channel

    def get_free_channel_ids(self,current_time):
        frees=[]
        for channel in self.db:
            if channel.is_free_open():
                frees.append(channel.id)
        return frees

    def get_free_channels(self,current_time):
        frees=[]
        for channel in self.db:
            if channel.is_free_open(current_time):
                frees.append(channel)
        return frees

    def get_detected_free_channel_ids(self,current_time):
        frees=[]
        for channel in self.db:
            if channel.detect_free(current_time):
                frees.append(channel.id)
        return frees

    def get_detected_free_channels(self,current_time):
        frees=[]
        for channel in self.db:
            if channel.detect_free(current_time):
                frees.append(channel)
        return frees

    def transmit(self,next_packet, channel_id):
        for channel in self.db:
            if channel.id==channel_id:
                channel.add(next_packet)

    def get_arrived_packets(self,CURRENT_TIME):
        arrived=[]
        for channel in self.db:
            candidate=channel.get_arrived_packets(CURRENT_TIME)
            if candidate is not None and len(candidate)>0:
                arrived.append(candidate)
        flat_list = [item for sublist in arrived for item in sublist]
        return flat_list

class Channel():
    def __init__(self,id,bitrate):
        self.id=id
        self.db=[]
        self.bitrate=bitrate
        self.propagation_time=myglobal.PROPAGATION_TIME
        self.detect_tx_in=0
        self.detect_tx_out=0
        self.tx_in=0
        self.tx_out=0
        self.trx_matrix=[]
        self.reserved_for_high=False

    def get_unlucky_list(self):
        mylist=[]
        if len(self.trx_matrix)>0:
            for i in range(0,myglobal.TOTAL_UNLUCKY_NODES):
                mylist.append(self.trx_matrix[-i-1])
        return mylist

    def is_free_open(self,current_time):
        if self.tx_in <= current_time and current_time <= self.tx_out:
            return False
        else:
            return True

    def get_total_time_to_tx(self,bytes):
        tx_time=(bytes*8)/self.bitrate
        return tx_time+self.propagation_time

    def detect_free(self,current_time):
        if self.detect_tx_in<=current_time and current_time<=self.detect_tx_out:
            return False
        else:
            return True

    def add(self,packet):
        self.db.append(packet)

    def delete_by_id(self,id):
        for element in self.db:
            if element.id==id:
                self.db.remove(element)
                break

    def get_arrived_packets(self,CURRENT_TIME):
        arrived=[]
        for packet in self.db:
            travel_time=(packet.packet_size*8)/self.bitrate
            if packet.time_trx_in+travel_time+self.propagation_time<=CURRENT_TIME:
                arrived.append(packet)
                self.db.remove(packet)
        return arrived




