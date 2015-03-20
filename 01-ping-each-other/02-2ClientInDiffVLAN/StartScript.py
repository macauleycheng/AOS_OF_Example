#*********************************************************************
#
# (C) Copyright Broadcom Corporation 2013-2014
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#*********************************************************************
#   This is a script intended
#   to use by Ryu OpenFlow controller
#
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
#
from ofdpa.config_parser import ConfigParser
from ofdpa.mods import Mods
#
import sys
import inspect, os
#
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import vlan
from ryu.lib.packet import arp
#
class StartScript(app_manager.RyuApp):

    _CONTEXTS = {'dpset': dpset.DPSet}
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(StartScript, self).__init__(*args, **kwargs)

    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def handler_datapath(self, ev):
        print "=Event DP="
        print "dpid: %i" % ev.dp.id
        if ev.enter:
            self.get_working_set(ev.dp)
      
        self.set_trap_arp_to_controller(ev.dp)

			
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        print "=Event PacketIn="
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        #print("packet in %s %s, %d, %s, msg: %s")%(eth.src, eth.dst, eth.ethertype, in_port, msg.data)    
        if(eth.ethertype == 0x0806):
		    self.packet_out_arp_reply(msg, in_port)
		
		
    def send_msg(self, dp, dir, processing_set):
        # 
        for filename in processing_set:
            #
            full_filename = dir +"/"+filename
            print "------------------------------------------------------------"
            print "processing file: %s" %  full_filename
            print "------------------------------------------------------------"
            #
            config = ConfigParser.get_config(full_filename)
            #
            for type in ConfigParser.get_config_type(config):
                #
                if (type == "flow_mod"):
                    mod_config = ConfigParser.get_flow_mod(config)
                    mod = Mods.create_flow_mod(dp, mod_config)
                    #
                elif (type == "group_mod"):
                    #
                    mod_config = ConfigParser.get_group_mod(config)
                    mod = Mods.create_group_mod(dp, mod_config)
                    #
                else:
                    print "no such type %s" % type				
                    return;
            print "mod len: %i" % sys.getsizeof(mod)
            dp.send_msg(mod)

    def packet_out_arp_reply(self, msg, in_port):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        #unpack received packet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        vlan_h = pkt.get_protocols(vlan.vlan)
        arp_pkt = pkt.get_protocols(arp.arp)[0]		

        print "arp op %x, src mac %s, src_ip %s, dst mac %s, dst_ip %s"%(arp_pkt.proto, arp_pkt.src_mac, arp_pkt.src_ip, arp_pkt.dst_mac, arp_pkt.dst_ip)
        if arp_pkt.opcode != arp.ARP_REQUEST:
            print "NOT arp request"

        #filter specify arp
        if (arp_pkt.src_ip == "0.0.0.0"):
            print "retunr because src_ip is 0.0.0.0"
            return;	
        if (arp_pkt.dst_mac == "ff:ff:ff:ff:ff:ff"):
            print "retunr because dst_mac is ff:ff:ff:ff:ff:ff"		
            return;
        #filter gratitious arp			
        if (arp_pkt.src_ip == arp_pkt.dst_ip):
            print "retunr because gratitious arp"
            return; 
        '''
        if(arp_pkt.dst_ip != "192.168.2.254" || arp_pkt.dst_ip!="192.168.1.254"):
            print "not gateway IP %s"%arp_pkt.dst_ip
            return;
        '''
        if(in_port == 1):		
            pkt_src_mac ="00:00:00:11:33:55"
        elif(in_port == 2):
            pkt_src_mac="00:00:00:22:44:66"		
        else:
            print "retunr because in port %d is not 1 and 2"%in_port
            return	
		
        #pack arp reply
        pkt_out = packet.Packet()
		#encode ethernet
        eth_out= ethernet.ethernet()
        eth_out.ethertype=0x0806
        eth_out.src=pkt_src_mac
        eth_out.dst=eth.src
        pkt_out.add_protocol(eth_out)
      
        #encode arp
        arp_reply=arp.arp()
        arp_reply.proto=arp_pkt.proto
        arp_reply.opcode=2		
        arp_reply.dst_mac=arp_pkt.src_mac
        arp_reply.dst_ip=arp_pkt.src_ip
        arp_reply.src_ip=arp_pkt.dst_ip
        arp_reply.src_mac=pkt_src_mac
        pkt_out.add_protocol(arp_reply)
		
        pkt_out.serialize()

        print "send out ARP replys"

        actions = [parser.OFPActionOutput(in_port, ofproto.OFPCML_NO_BUFFER)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER ,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions, data=pkt_out.data)	
        datapath.send_msg(out)	 	
	
	

    def add_flow(self, datapath , table_id, priority , match , inst):
       ofproto = datapath.ofproto
       parser = datapath.ofproto_parser
       mod = parser.OFPFlowMod(datapath=datapath, table_id=table_id, priority=priority ,
                               match=match , instructions=inst)
       datapath.send_msg(mod)
	   
    def set_trap_arp_to_controller(self, dp):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser	
        #ARP/ARP-reply goto controller BY ACL
        match = parser.OFPMatch(eth_type=0x0806)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        self.add_flow(dp , 60, 1, match , inst)	
		
    def get_working_set(self, dp):
        dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))	
        working_set = ConfigParser.get_working_set(dir +"/working_set.json")
        self.send_msg(dp, dir, working_set)
