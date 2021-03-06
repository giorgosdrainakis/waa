import math
import random
from waa import myglobal
from waa.channel import *
from waa.traffic import Control_Packet

class Decoder:
    def __init__(self):
        self.db=[]

    def get_total_big_packs_waiting(self):
        total_big_packs=0
        for node in self.db:
            if len(node.med_buffer) > 0:
                if node.med_buffer[0].slot is None and node.med_buffer[0].size == myglobal.MAX_PACKET_SIZE:
                    total_big_packs=total_big_packs+1
            if len(node.low_buffer) > 0:
                if node.low_buffer[0].slot is None and node.low_buffer[0].size == myglobal.MAX_PACKET_SIZE:
                    total_big_packs=total_big_packs+1
        return total_big_packs


    def fill_with_big_packs(self,node_id, ch_id, start_slot):
        is_big_filled=False
        for node in self.db:
            if node.node_id == node_id:
                if len(node.med_buffer)>0:
                    if node.med_buffer[0].slot is None and node.med_buffer[0].size == myglobal.MAX_PACKET_SIZE:
                        node.med_buffer[0].slot = start_slot
                        node.med_buffer[0].channel = ch_id
                        is_big_filled = True
                if not is_big_filled:
                    if len(node.low_buffer) > 0:
                        if node.low_buffer[0].slot is None and node.low_buffer[0].size == myglobal.MAX_PACKET_SIZE:
                            node.low_buffer[0].slot = start_slot
                            node.low_buffer[0].channel = ch_id
                            is_big_filled = True
                return is_big_filled

    def fill_with_small_packs(self,node_id,ch_id,max_pack_num,start_slot,lucky_number):

   #     print('Debug fill with small for node_id' +str(node_id)+',ch'+str(ch_id)+' slot'+str(start_slot))
        packs_filled=self.fill_high(node_id, max_pack_num, start_slot, ch_id)

        if packs_filled<max_pack_num:
            if lucky_number <= 7:
                packs_filled=packs_filled+self.fill_med(node_id, max_pack_num-packs_filled, start_slot+packs_filled, ch_id)
                if packs_filled < max_pack_num:
                    packs_filled = packs_filled + self.fill_low(node_id, max_pack_num - packs_filled, start_slot+packs_filled, ch_id)
            else:
                packs_filled=packs_filled+self.fill_low(node_id, max_pack_num-packs_filled, start_slot+packs_filled, ch_id)
                if packs_filled < max_pack_num:
                    packs_filled = packs_filled + self.fill_med(node_id, max_pack_num - packs_filled, start_slot+packs_filled, ch_id)

        return packs_filled


    def fill_high(self,node_id,max_pack_num,start_slot,ch_id):
        for node in self.db:
            if node.node_id==node_id:
                packs_filled=0
                i=0
                while packs_filled<max_pack_num and i<len(node.high_buffer):
                    if node.high_buffer[i].slot is None and node.high_buffer[i].size==64:
                        node.high_buffer[i].slot=start_slot+packs_filled
                        node.high_buffer[i].channel=ch_id
                        packs_filled=packs_filled+1
                    else:
                        pass
                    i=i+1
                return packs_filled

    def fill_med(self,node_id,max_pack_num,start_slot,ch_id):
        for node in self.db:
            if node.node_id==node_id:
                packs_filled=0
                i=0
                big_found=False
                while packs_filled<max_pack_num and i<len(node.med_buffer) and (not big_found):
                    if node.med_buffer[i].size==myglobal.MAX_PACKET_SIZE:
                        big_found=True
                    else:
                        if node.med_buffer[i].slot is None:
                            node.med_buffer[i].slot=start_slot+packs_filled
                            node.med_buffer[i].channel=ch_id
                            packs_filled=packs_filled+1
                    i=i+1
                return packs_filled

    def fill_low(self,node_id,max_pack_num,start_slot,ch_id):
        for node in self.db:
            if node.node_id==node_id:
                packs_filled=0
                i=0
                big_found=False
                while packs_filled<max_pack_num and i<len(node.low_buffer) and (not big_found):
                    if node.low_buffer[i].size==myglobal.MAX_PACKET_SIZE:
                        big_found=True
                    else:
                        if node.low_buffer[i].slot is None:
                            node.low_buffer[i].slot=start_slot+packs_filled
                            node.low_buffer[i].channel=ch_id
                            packs_filled=packs_filled+1
                    i=i+1
                return packs_filled

class Decoded_Node:
    def __init__(self):
        self.node_id=None
        self.high_buffer=[]
        self.med_buffer=[]
        self.low_buffer=[]
class Decoded_Pack:
    def __init__(self):
        self.size=None
        self.slot=None
        self.channel=None

class Nodes:
    def __init__(self):
        self.db=[]
        self.channels=Channels()
        self.control_channel=None
        self.current_cycle=0

    def add_new_packets_to_buffers(self,current_time):
        for node in self.db:
            node.add_new_packets_to_buffers(current_time)

    def geodranas_consumption(self,current_time):
        for node in self.db:
            if node.id==16:
                node.geodranas_consume(1500,current_time)

    def check_arrival_WAA(self,current_time):
        # check arrivals
        total_packet_arrived_list=[]
        for node in self.db:
            node.check_control_arrival_WAA(current_time)
            total_packet_arrived_list.extend(node.check_data_arrival_WAA(current_time))

        for pack in total_packet_arrived_list:
            if pack.destination_tor==1:
                arrival_id=pack.destination_id
            else:
                arrival_id=16
            for node in self.db:
                if node.id==arrival_id:
                    node.add_reception(pack)

    def process_new_cycle(self,current_time):
        total_nodes = len(self.db)
        cycle_time=self.get_per_cycle_time()
        total_slots=int(myglobal.CYCLE_SIZE/myglobal.MIN_PACKET_SIZE)
        cycle_slot_time=cycle_time/total_slots
        control_bitsize_per_node=myglobal.CONTROL_MSG_PACKS_PER_BUFF*myglobal.TOTAL_BUFFS_PER_NODE*myglobal.CONTROL_MINIPACK_SIZE
        control_cycle_slot_time=control_bitsize_per_node/self.channels.get_common_bitrate()
        entered_new_cycle=(current_time>=cycle_time*self.current_cycle)
        if entered_new_cycle:
            print('-----------Entered new cycle=' + str(self.current_cycle) + ' at=' + str(current_time))
            control_msg = self.build_new_control_message()
            decoder=self.run_distributed_algo(control_msg)

            for node in self.db:
                node.process_new_cycle(current_time,decoder,cycle_time,cycle_slot_time,control_cycle_slot_time,
                                       self.current_cycle,self.channels,self.control_channel,total_nodes)

            self.current_cycle=self.current_cycle+1


    def build_new_control_message(self):
        msg=[]
        bonus=None
        for node in self.db:
            if len(node.control_sent)==1:
                msg.append(node.control_sent[0])
            elif len(node.control_sent)==2:
                msg.append(node.control_sent[0])
                bonus=node.control_sent[1]
        if bonus is not None:
            msg.append(bonus)
        for node in self.db:
            node.control_sent=[]
        return msg

    def decode_control_msg(self,control_msg,cut1,cut2,cut3,node_id_diff):
        decoder=Decoder()

        for control_pack in control_msg:
            decoded_node=Decoded_Node()
            decoded_node.node_id=control_pack.source_id
            if control_pack.is_bonus_packet:
                continue
            db_med_1500=0
            db_med_64=0
            db_low_1500=0
            db_low_64 = 0
            for minipack in control_pack.minipack_list:
                src_bit_id,dest_bit_id,cl,subcl= minipack[0:cut1], minipack[cut1:cut2], minipack[cut2:cut3], minipack[cut3]
                if decoded_node.node_id!=int(src_bit_id,2)+node_id_diff:
                    print(str('sync ERROR - checking different packets ids'))
                    continue
                decoded_pack=Decoded_Pack()
                if cl=='00':
                    decoded_pack.size=myglobal.MIN_PACKET_SIZE
                    decoded_node.high_buffer.append(decoded_pack)
                elif cl=='01' :
                    if subcl=='0':
                        decoded_pack.size=myglobal.MIN_PACKET_SIZE
                        db_med_64 = db_med_64 + 1
                    elif subcl=='1':
                        decoded_pack.size=myglobal.MAX_PACKET_SIZE
                        db_med_1500=db_med_1500+1
                    else:
                        print(str('coding ERROR - unknown size:') + str(subcl))
                        continue
                    decoded_node.med_buffer.append(decoded_pack)
                elif cl=='10':
                    if subcl=='0':
                        decoded_pack.size=myglobal.MIN_PACKET_SIZE
                        db_low_64 = db_low_64 + 1
                    elif subcl=='1':
                        decoded_pack.size=myglobal.MAX_PACKET_SIZE
                        db_low_1500 = db_low_1500 + 1
                    else:
                        print(str('coding ERROR - unknown size:') + str(subcl))
                        continue
                    decoded_node.low_buffer.append(decoded_pack)
                else:
                    print(str('coding ERROR - unknown QOS:')+str(cl))
                    continue
            decoder.db.append(decoded_node)

            print('I decoded for node '+str(decoded_node.node_id)+' buff len h-m-l='+
                  str(len(decoded_node.high_buffer))+'-'+str(len(decoded_node.med_buffer))+'('+str(db_med_64)+
                  ','+str(db_med_1500)+')'+'-'+
                  str(len(decoded_node.low_buffer))+'('+str(db_low_64)+','+str(db_low_1500)+')'+
                  ',minipacklist='+str(len(control_pack.minipack_list)))

        return decoder

    def build_trx_matrices(self,lucky_node):
        total_nodes = len(self.db)

        A = []
        for i in range(0, total_nodes):
            if lucky_node + i <= total_nodes:
                A.append(lucky_node + i)
            else:
                A.append(lucky_node + i - total_nodes)

        for i in range(0,len(self.channels.db)):
            if i==0:
                self.channels.db[i].trx_matrix=A
            else:
                previous_matrix=self.channels.db[i-1].trx_matrix
                self.channels.db[i].trx_matrix=previous_matrix[1:] + [previous_matrix[0]]

    def run_distributed_algo(self,control_msg):
        if len(control_msg)==0:
            return None
        lucky_node_bit_id, lucky_number=self.get_s_p_params(control_msg,break_position=myglobal.BREAK_POSITION)
        lucky_node=lucky_node_bit_id+myglobal.ID_DIFF
        decoder=self.decode_control_msg(control_msg,cut1=myglobal.CUT_1,cut2=myglobal.CUT_2,cut3=myglobal.CUT_3,
                                        node_id_diff=myglobal.ID_DIFF)
        self.build_trx_matrices(lucky_node)

        #Assign all channels to big packets first!
        if myglobal.ASSIGN_CHANNEL_POLICY=='ALL_BIG':
            for ch in self.channels.db:
                start_slot = 0
                i = 0
                is_big_filled = False
                while (i < len(ch.trx_matrix) and (not is_big_filled)):
                    node_id = ch.trx_matrix[i]
                    is_big_filled = decoder.fill_with_big_packs(node_id, ch.id, start_slot)
                    i = i + 1
                if not is_big_filled:
                    start_slot = 0
                    for i in range(0, len(ch.trx_matrix)):
                        node_id = ch.trx_matrix[i]
                        # check if current node belongs in lucky or unlucky family
                        if node_id in ch.get_unlucky_list():
                            max_pack_num = myglobal.UNLUCKY_SLOT_LEN
                        else:
                            max_pack_num = myglobal.LUCKY_SLOT_LEN
                        packs_filled = decoder.fill_with_small_packs(node_id, ch.id, max_pack_num, start_slot,
                                                                     lucky_number)
                        if packs_filled > 0:
                            start_slot = start_slot + packs_filled
                else:
                    print('Debug: Will TRX big pack in ch=' + str(ch.id))
        else:
            # Assign at least the last channel to potential big packets
            ch = self.channels.db[-1]
            start_slot = 0
            i = 0
            is_big_filled = False
            while (i < len(ch.trx_matrix) and (not is_big_filled)):
                node_id = ch.trx_matrix[i]
                is_big_filled = decoder.fill_with_big_packs(node_id, ch.id, start_slot)
                i = i + 1
            if not is_big_filled:
                start_slot = 0
                for i in range(0, len(ch.trx_matrix)):
                    node_id = ch.trx_matrix[i]
                    # check if current node belongs in lucky or unlucky family
                    if node_id in ch.get_unlucky_list():
                        max_pack_num = myglobal.UNLUCKY_SLOT_LEN
                    else:
                        max_pack_num = myglobal.LUCKY_SLOT_LEN
                    packs_filled = decoder.fill_with_small_packs(node_id, ch.id, max_pack_num, start_slot,
                                                                 lucky_number)
                    if packs_filled > 0:
                        start_slot = start_slot + packs_filled
            else:
                print('Debug: Will TRX big pack in ch=' + str(ch.id))

            # rest of the channels will be filled with small, unless not enough
            current_ch_list=[x for x in self.channels.db if (x.id!=ch.id)]
            for ch in current_ch_list:
                start_slot = 0
                for i in range(0, len(ch.trx_matrix)):
                    node_id = ch.trx_matrix[i]
                    if node_id in ch.get_unlucky_list():
                        max_pack_num = myglobal.UNLUCKY_SLOT_LEN
                    else:
                        max_pack_num = myglobal.LUCKY_SLOT_LEN
                    packs_filled = decoder.fill_with_small_packs(node_id, ch.id, max_pack_num, start_slot, lucky_number)
                    if packs_filled > 0:
                        start_slot = start_slot + packs_filled
                if start_slot==0: # no small packets found
                    i = 0
                    is_big_filled = False
                    while (i < len(ch.trx_matrix) and (not is_big_filled)):
                        node_id = ch.trx_matrix[i]
                        is_big_filled = decoder.fill_with_big_packs(node_id, ch.id, start_slot)
                        i = i + 1
                    if is_big_filled:
                        print('Debug: Will TRX big pack in ch=' + str(ch.id))

        # DEBUGG
        total_str=[]
        for node in decoder.db:
            mystr='Node:'+str(node.node_id)
            high_str=[]
            for pack in node.high_buffer:
                if pack.slot is not None:
                    newstr=str(pack.channel)+'.'+str(pack.slot).zfill(2)
                    high_str.append(newstr)

            med_str = []
            for pack in node.med_buffer:
                if pack.slot is not None:
                    newstr=str(pack.channel)+'.'+str(pack.slot).zfill(2)
                    med_str.append(newstr)

            low_str = []
            for pack in node.low_buffer:
                if pack.slot is not None:
                    newstr=str(pack.channel)+'.'+str(pack.slot).zfill(2)
                    low_str.append(newstr)

            print(str(mystr)+' high slots:'+str(high_str)+' med slots:'+str(med_str)+' low slots:'+str(low_str))
            total_str=total_str+high_str+med_str+low_str
        total_str=sorted(total_str)
        print(str(total_str))
        return decoder

    def get_s_p_params(self,control_msg,break_position):
        bonus_pack=None
        for pack in control_msg:
            if pack.is_bonus_packet:
                bonus_pack=pack
                break
        if bonus_pack is not None:
            s3, p4 = bonus_pack.bonus_info[:break_position], bonus_pack.bonus_info[break_position:]
            lucky_node_bit_id = int(s3, 2)
            lucky_number = int(p4, 2)
        else:
            lucky_node_bit_id=myglobal.DEFAULT_UNLUCKY_NODE_ID-myglobal.ID_DIFF
            lucky_number=myglobal.DEFAULT_LUCKY_NUM
        return lucky_node_bit_id, lucky_number

    def get_per_cycle_time(self):
        return (myglobal.MAX_PACKET_SIZE*8)/self.channels.get_common_bitrate()

    def transmit_WAA(self, current_time):
        for node in self.db:
            node.transmit_control(current_time)
            if self.current_cycle>0:
                node.transmit_data(current_time)

    def have_buffers_packets(self):
        for node in self.db:
            if node.have_buffers_packets():
                return True

    def add_new(self,node):
        self.db.append(node)

    def get_node_from_id(self,id):
        for node in self.db:
            if node.id==id:
                return node

    def decrement(self):
        #back_times=[]
        for node in self.db:
            node.waiting=max(0,node.waiting-myglobal.timestep)
            node.C_idle=max(0,node.C_idle-myglobal.timestep)
            node.C_load = max(0, node.C_load - myglobal.timestep)
            node.C_send = max(0, node.C_send - myglobal.timestep)
            if node.flag_A=='competition':
                node.backoff_time = max(0, node.backoff_time - myglobal.timestep)
            #back_times.append(node.backoff_time)
        #print(str(back_times))

    def get_next_packet(self,current_time):
        for node in self.db:
            candidate=node.get_next_packet(current_time)
            if candidate is not None:
                return candidate
        return None

class Node:
    def __init__(self,id,traffic):
        self.id=id
        self.traffic=traffic
        self.buffer_low=None
        self.buffer_med=None
        self.buffer_high=None

        self.data_meta_buffer=[]
        self.data_dropped=[]
        self.data_sent=[]

        self.control_meta_buffer=[]
        self.control_sent=[]

        self.receiver=[]
        self.consumed=[]

    def geodranas_consume(self,size,curr_time):
        current_size = 0
        for item in self.receiver:
            if item.packet_size+current_size<=size:
                current_size = current_size+item.packet_size
                item.consume_time=curr_time
                self.consumed.append(item)
                self.receiver.remove(item)
                print('Consuming in TOR for item_ID:'+str(item.packet_id)+'with size='+str(item.packet_size))
            else:
                break

    def add_reception(self,packet):
        self.receiver.append(packet)

    def decode_previous_cycle(self, decoder, cycle_time, cycle_slot_time, current_cycle, data_channels):
        if decoder is None:
            return

        decoded_node=None
        for node in decoder.db:
            if node.node_id==self.id:
                decoded_node=node
        
        if decoded_node is None:
            return

        i=0
        while i<len(decoded_node.high_buffer) and (decoded_node.high_buffer[i].slot is not None):
            try:
                new_pack=self.buffer_high.get_next_packet()
            except:
                print('error in node '+str(self.id))
                exit(-1)
            new_pack.channel_id = decoded_node.high_buffer[i].channel
            new_pack.time_trx_in=(current_cycle+0)*cycle_time+decoded_node.high_buffer[i].slot*cycle_slot_time
            mych=data_channels.get_channel_from_id(new_pack.channel_id)
            new_pack.time_trx_out = new_pack.time_trx_in + mych.get_total_time_to_tx(new_pack.packet_size)
            self.data_meta_buffer.append(new_pack)
            i=i+1

        i=0
        while i<len(decoded_node.med_buffer) and (decoded_node.med_buffer[i].slot is not None):
            new_pack=self.buffer_med.get_next_packet()
            new_pack.channel_id = decoded_node.med_buffer[i].channel
            new_pack.time_trx_in=(current_cycle+0)*cycle_time+decoded_node.med_buffer[i].slot*cycle_slot_time
            mych=data_channels.get_channel_from_id(new_pack.channel_id)
            new_pack.time_trx_out = new_pack.time_trx_in + mych.get_total_time_to_tx(new_pack.packet_size)
            self.data_meta_buffer.append(new_pack)
            i=i+1

        i=0
        while i<len(decoded_node.low_buffer) and (decoded_node.low_buffer[i].slot is not None):
            new_pack=self.buffer_low.get_next_packet()
            new_pack.channel_id = decoded_node.low_buffer[i].channel
            new_pack.time_trx_in=(current_cycle+0)*cycle_time+decoded_node.low_buffer[i].slot*cycle_slot_time
            mych=data_channels.get_channel_from_id(new_pack.channel_id)
            new_pack.time_trx_out = new_pack.time_trx_in + mych.get_total_time_to_tx(new_pack.packet_size)
            self.data_meta_buffer.append(new_pack)
            i=i+1

    def build_next_rounds_control_msg(self,current_time,cycle_time, control_cycle_slot_time,
                          current_cycle, control_channel):
        mymsg=Control_Packet(current_time,self.id)
        minipack_list=[]
        i=0
        for pack in self.buffer_high.db:
            if i<myglobal.CONTROL_MSG_PACKS_PER_BUFF:
                strr=myglobal.STR_SOURCE_DEST_ID
                src_bit_id=strr.format(self.id-myglobal.ID_DIFF)
                dest_bit_id=strr.format(pack.destination_id-myglobal.ID_DIFF)
                cl='00'
                subcl='0'
                total_str=src_bit_id+dest_bit_id+cl+subcl
                minipack_list.append(total_str)
            i=i+1

        mydbg_high=min(i,myglobal.CONTROL_MSG_PACKS_PER_BUFF)

        i=0
        for pack in self.buffer_med.db:
            if i<myglobal.CONTROL_MSG_PACKS_PER_BUFF:
                strr=myglobal.STR_SOURCE_DEST_ID
                src_bit_id=strr.format(self.id-myglobal.ID_DIFF)
                dest_bit_id=strr.format(pack.destination_id-myglobal.ID_DIFF)
                cl='01'
                if pack.packet_size==myglobal.MIN_PACKET_SIZE:
                    subcl='0'
                elif pack.packet_size==myglobal.MAX_PACKET_SIZE:
                    subcl = '1'
                total_str=src_bit_id+dest_bit_id+cl+subcl
                minipack_list.append(total_str)
            i=i+1

        mydbg_med=min(i,myglobal.CONTROL_MSG_PACKS_PER_BUFF)

        i=0
        for pack in self.buffer_low.db:
            if i<myglobal.CONTROL_MSG_PACKS_PER_BUFF:
                strr=myglobal.STR_SOURCE_DEST_ID
                src_bit_id=strr.format(self.id-myglobal.ID_DIFF)
                dest_bit_id=strr.format(pack.destination_id-myglobal.ID_DIFF)
                cl = '10'
                if pack.packet_size == myglobal.MIN_PACKET_SIZE:
                    subcl = '0'
                elif pack.packet_size == myglobal.MAX_PACKET_SIZE:
                    subcl = '1'
                total_str=src_bit_id+dest_bit_id+cl+subcl
                minipack_list.append(total_str)
            i=i+1

        mydbg_low=min(i,myglobal.CONTROL_MSG_PACKS_PER_BUFF)

        mymsg.minipack_list=minipack_list
        bit_packet_size=myglobal.CONTROL_MSG_PACKS_PER_BUFF*myglobal.TOTAL_BUFFS_PER_NODE*\
                              myglobal.CONTROL_MINIPACK_SIZE #bytes
        mymsg.packet_size=bit_packet_size/8
        myslot=self.id-myglobal.ID_DIFF
        mymsg.time_trx_in=(current_cycle+0)*cycle_time+myslot*control_cycle_slot_time
        mymsg.channel_id=control_channel.id
        mymsg.time_trx_out=mymsg.time_trx_in+control_channel.get_total_time_to_tx(mymsg.packet_size)
        mymsg.is_bonus_packet=False
        self.control_meta_buffer.append(mymsg)

        print('nodes send info with id='+str(self.id)+' and high-med-low-total='+str(mydbg_high)+'-'+str(mydbg_med)+'-'+str(mydbg_low)+'-'+str(len(minipack_list)))


    def build_bonus_msg(self,current_time,decoder,cycle_time, control_cycle_slot_time,
                          current_cycle, data_channels,control_channel,total_nodes):

        unlucky_node_id=data_channels.get_one_unlucky_node_id()

        if self.id==unlucky_node_id:
            max_node_id=total_nodes-myglobal.ID_DIFF
            r = random.randint(0, max_node_id)
            strr=myglobal.STR_SOURCE_DEST_ID
            s = strr.format(r)
            r = random.randint(1, 10)
            p = "{0:04b}".format(r)
            info=s+p
            mybn=Control_Packet(current_time,self.id)
            mybn.bonus_info=info
            mybn.is_bonus_packet=True
            mybn.packet_size=myglobal.BONUS_MSG_BITSIZE/8 #bytes
            myslot=total_nodes
            mybn.time_trx_in = (current_cycle+0) * cycle_time + myslot * control_cycle_slot_time
            mybn.channel_id = control_channel.id
            mybn.time_trx_out = mybn.time_trx_in + control_channel.get_total_time_to_tx(mybn.packet_size)
            self.control_meta_buffer.append(mybn)

    def process_new_cycle(self,current_time,decoder,cycle_time, cycle_slot_time,control_cycle_slot_time,
                          current_cycle, data_channels,control_channel,total_nodes):

        self.decode_previous_cycle(decoder, cycle_time, cycle_slot_time, current_cycle, data_channels)
        self.build_next_rounds_control_msg(current_time, cycle_time, control_cycle_slot_time,
                                          current_cycle, control_channel)
        self.build_bonus_msg(current_time,decoder,cycle_time, control_cycle_slot_time,
                          current_cycle, data_channels,control_channel,total_nodes)

    def transmit_control(self,current_time):
        for control_pack in self.control_meta_buffer:
            if control_pack.time_trx_in<=current_time and (not control_pack.annotated):
                print('Transmitting control packet from node=' + str(self.id))
                control_pack.annotated=True

    def transmit_data(self,current_time):
        for data_pack in self.data_meta_buffer:
            if data_pack.time_trx_in<=current_time and (not data_pack.annotated):
                print('Transmitting data packet with ID='+str(data_pack.packet_id)+' from node=' + str(self.id))
                data_pack.annotated = True

    def check_data_arrival_WAA(self,current_time):
        total_packet_arrived_list=[]
        for pack in self.data_meta_buffer:
            has_packet_arrived=pack.time_trx_in<pack.time_trx_out and pack.time_trx_out<=current_time
            if has_packet_arrived:
                pack.time_trx_out=current_time
                self.data_sent.append(pack)
                self.data_meta_buffer.remove(pack)
                total_packet_arrived_list.append(pack)
                print('Received data packet with ID='+str(pack.packet_id)+' from node=' + str(pack.source_id))
            else: #packet has not arrived
                pass
        return total_packet_arrived_list
    def check_control_arrival_WAA(self, current_time):
        for pack in self.control_meta_buffer:
            has_packet_arrived=pack.time_trx_in<pack.time_trx_out and pack.time_trx_out<=current_time
            if has_packet_arrived:
                pack.time_trx_out=current_time
                self.control_sent.append(pack)
                self.control_meta_buffer.remove(pack)
                print('Received control packet from node=' + str(pack.source_id))
            else: #packet has not arrived
                pass

    def print_buff(self):
        mystr='-'+str(self.buffer_low.get_current_size())+'-'+str(self.buffer_med.get_current_size())+'-'+str(self.buffer_high.get_current_size())
        return mystr
    def have_buffers_packets(self):
        if self.buffer_low.has_packets() or self.buffer_med.has_packets() or self.buffer_high.has_packets():
            return True
    def add_new_packets_to_buffers(self,current_time):
        new_packets=self.traffic.get_new_packets(current_time)
        for packet in new_packets:
            is_in_buffer=False
            if packet.packet_qos=='low':
                is_in_buffer=self.buffer_low.add(packet,current_time)
                #('Added packet=' + str(packet.packet_id) + ' in low buffer node=' + str(self.id))
            elif packet.packet_qos=='med':
                is_in_buffer=self.buffer_med.add(packet,current_time)
                #print('Added packet=' + str(packet.packet_id) + ' in  med buffer node=' + str(self.id))
            elif packet.packet_qos=='high':
                is_in_buffer=self.buffer_high.add(packet,current_time)
                #print('Added packet=' + str(packet.packet_id) + ' in high buffer node=' + str(self.id))
            if not is_in_buffer:
                print('Dropped packet='+str(packet.packet_id)+' in node='+str(self.id))
                self.data_dropped.append(packet)

    def get_next_packet(self):
        if self.buffer_high.has_packets():
            return self.buffer_high.get_next_packet()
        elif self.buffer_med.has_packets():
            if self.buffer_low.has_packets():
                lucky=random.uniform(0, 1)
                if lucky<0.3:
                    return self.buffer_low.get_next_packet()
                else:
                    return self.buffer_med.get_next_packet()
            else:
                return self.buffer_med.get_next_packet()
        elif self.buffer_low.has_packets():
            return self.buffer_low.get_next_packet()
        else:
            return None









