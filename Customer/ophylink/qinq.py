from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3


class qinq(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	
    def __init__(self, *args, **kwargs):
        super( qinq, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto		
        parser = datapath.ofproto_parser	
		
        self.clearAllFlowsAndGroups(datapath)

        #create l2_interface_group, output port 2 vlan 10 tagged
        actions = [parser.OFPActionOutput(2) ]
        buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]       
        self.add_group(datapath, ofproto.OFPGT_INDIRECT, 0x000a0002, buckets)
        
        #add acl table
        actions = [parser.OFPActionGroup(0x000a0002)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        match = parser.OFPMatch()
        match.set_in_port(1)
        self.add_flow(datapath ,60 ,1, match , inst)  

        #add vlan flow, match (untagged, inport 1) add vlan tag 10
        actions = [parser.OFPActionSetField(vlan_vid=1)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                parser.OFPInstructionGotoTable(20)]
        match = parser.OFPMatch()
        match.set_vlan_vid_masked(0, 0x0fff)
        match.set_in_port(1)
        self.add_flow(datapath ,10 ,1, match , inst)  
        #add vlan flow, match (vlan tag 1, inport 1) add vlan tag 10
        actions = [parser.OFPActionPushVlan(),
                   parser.OFPActionSetField(vlan_vid=10)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                parser.OFPInstructionGotoTable(20)]
        match = parser.OFPMatch()
        match.set_vlan_vid_masked(1, 0x1fff)
        match.set_in_port(1)
        self.add_flow(datapath ,10 ,1, match , inst)	

        
    @set_ev_cls(ofp_event.EventOFPPacketIn , MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
		
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
                               match=match, instructions=inst)
       datapath.send_msg(mod)

    def del_flow(self, datapath , table_id, priority , match , inst):
       ofproto = datapath.ofproto
       parser = datapath.ofproto_parser
       mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE, table_id=table_id, priority=priority,
	                           out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                               match=match , instructions=inst)
       datapath.send_msg(mod)

       
       
#app_manager.require_app('00-table-group-unit-test.22-create52PortJoin4Kvlan.AllPortJoinAllVLANs')