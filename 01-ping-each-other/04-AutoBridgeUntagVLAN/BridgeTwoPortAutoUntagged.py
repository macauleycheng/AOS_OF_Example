from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import vlan
from ryu.lib import mac

class BridgeTwoPortAuto(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	
    #define group id
    l2_flood_group=0x40010001
    l2_intf_p1_group=0x10001
    l2_intf_p2_group=0x10002
    l2_intf_p3_group=0x10003
	
    def __init__(self, *args, **kwargs):
        super(BridgeTwoPortAuto , self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
		
        self.clearAllFlowsAndGroups(datapath)
		
        self.addDefaultGroupFlows(datapath)
		
    def addDefaultGroupFlows(self, datapath):	
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser	
        
        #ARP/ARP-reply goto controller BY ACL
        match = parser.OFPMatch(eth_type=0x0806)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        self.add_flow(datapath , 60, 1, match , inst)

        #create group forward to port 1, untagged
        actions = [parser.OFPActionOutput(port=1), parser.OFPActionPopVlan()]
        buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
        self.add_group(datapath, ofproto.OFPGT_INDIRECT, self.l2_intf_p1_group, buckets)
        #create group forward to port 2, untagged
        actions = [parser.OFPActionOutput(port=2), parser.OFPActionPopVlan()]
        buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]		
        self.add_group(datapath, ofproto.OFPGT_INDIRECT, self.l2_intf_p2_group, buckets)		
        #create group forward to port 3, tagged
        actions = [parser.OFPActionOutput(port=3)]
        buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]		
        self.add_group(datapath, ofproto.OFPGT_INDIRECT, self.l2_intf_p3_group, buckets)		

		#add group flood to port 1 and 2
        bk1_actions = [parser.OFPActionGroup(self.l2_intf_p1_group)]
        bk2_actions = [parser.OFPActionGroup(self.l2_intf_p2_group)]
        buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=bk1_actions),
                   parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=bk2_actions)]
        bk3_actions = [parser.OFPActionGroup(self.l2_intf_p3_group)]
        buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=bk3_actions)]
        self.add_group(datapath, ofproto.OFPGT_ALL, self.l2_flood_group, buckets)
		
        '''
        NOTE: for untag/tag, it need add together, 
		      for untagged packet vlan=1, so tagged vlan 1 
		      packet shall add too.
        '''		
		#add port 1 untagged join vlan 1
        actions = [parser.OFPActionSetField(vlan_vid=1)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                parser.OFPInstructionGotoTable(20)]
        match = parser.OFPMatch()
        match.set_vlan_vid_masked(0, 0x0fff)
        match.set_in_port(1)
        self.add_flow(datapath ,10 ,1, match , inst)		
		#add port 2 untagged join vlan 1
        actions = [parser.OFPActionSetField(vlan_vid=1)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                parser.OFPInstructionGotoTable(20)]
        match = parser.OFPMatch()
        match.set_vlan_vid_masked(0, 0x0fff)		
        match.set_in_port(2)
        self.add_flow(datapath ,10 ,1, match , inst)
		#add port 1 tagged join vlan 1
        actions = [parser.OFPActionSetField(vlan_vid=1)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                parser.OFPInstructionGotoTable(20)]
        match = parser.OFPMatch()
        match.set_vlan_vid_masked(1, 0x1fff)
        match.set_in_port(1)
        self.add_flow(datapath ,10 ,1, match , inst)		
		#add port 2 untagged join vlan 1
        actions = [parser.OFPActionSetField(vlan_vid=1)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                parser.OFPInstructionGotoTable(20)]
        match = parser.OFPMatch()
        match.set_vlan_vid_masked(1, 0x1fff)
        match.set_in_port(2)
        self.add_flow(datapath ,10 ,1, match , inst)

        
		#add dst=DLF, vid=1 flow by l2_flood_group
        #match = parser.OFPMatch()
        #match.set_dl_dst_masked(mac.haddr_to_bin('ff:ff:ff:ff:ff:ff'), 
        #                        mac.haddr_to_bin('ff:ff:ff:ff:ff:ff'))
        #match.set_vlan_vid(1)		
        #actions = [parser.OFPActionGroup(self.l2_flood_group)]
        #inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
        #        parser.OFPInstructionGotoTable(60)]
        #self.add_flow(datapath , 50, 1, match, inst)

		#add dst=DLF, vid=1 flow to controller
        match = parser.OFPMatch()
        match.set_vlan_vid(1)
        actions_c = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        actions_g = [parser.OFPActionGroup(self.l2_flood_group)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions_c),
		        parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions_g),
                parser.OFPInstructionGotoTable(60)]
        self.add_flow(datapath , 50, 1, match, inst)		

    def clearAllFlowsAndGroups(self, datapath):	
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
        #clear all flows
        match = parser.OFPMatch()
        self.del_flow(datapath , ofproto.OFPTT_ALL, 0, match, inst=[])
        #clear all groups
        buckets = []
        self.del_group(datapath, ofproto.OFPGT_INDIRECT, ofproto.OFPG_ALL, buckets)	

    def add_group(self, datapath, type, group_id, buckets):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
        req = parser.OFPGroupMod(datapath, ofproto.OFPGC_ADD,
                                 type, group_id, buckets)
        datapath.send_msg(req)		

    def del_group(self, datapath, type, group_id, buckets):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
        req = parser.OFPGroupMod(datapath, ofproto.OFPGC_DELETE,
                                 type, group_id, buckets)
        datapath.send_msg(req)	
		
    def add_flow(self, datapath , table_id, priority , match , inst):
       ofproto = datapath.ofproto
       parser = datapath.ofproto_parser
       mod = parser.OFPFlowMod(datapath=datapath, table_id=table_id, priority=priority ,
                               match=match , instructions=inst)
       datapath.send_msg(mod)

    def del_flow(self, datapath , table_id, priority , match , inst):
       ofproto = datapath.ofproto
       parser = datapath.ofproto_parser
       mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE, table_id=table_id, priority=priority,
	                           out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                               match=match , instructions=inst)
       datapath.send_msg(mod)
	   
    @set_ev_cls(ofp_event.EventOFPPacketIn , MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        vlan_h = pkt.get_protocols(vlan.vlan)
        vid=0
        if len(vlan_h) != 0:
            vid = vlan_h[0]
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        print("packet in %s %d %s %s %s")%(dpid, vid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        if src not in self.mac_to_port[dpid]:
            print "add table 50"
            if in_port == 1:
               actions = [parser.OFPActionGroup(self.l2_intf_p1_group)]
            elif in_port == 2:
               actions = [parser.OFPActionGroup(self.l2_intf_p2_group)]		
			
            match = parser.OFPMatch(vlan_vid=1, eth_dst=src)
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                parser.OFPInstructionGotoTable(60)]			
            self.add_flow(datapath ,50 ,1, match , inst)
			
        self.mac_to_port[dpid][src] = in_port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        print "out_port %d"%out_port
			
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        actions = [parser.OFPActionOutput(out_port)]
        out = parser.OFPPacketOut(datapath=datapath , buffer_id=msg.buffer_id ,
                                  in_port=in_port , actions=actions , data=data)
        datapath.send_msg(out)	   