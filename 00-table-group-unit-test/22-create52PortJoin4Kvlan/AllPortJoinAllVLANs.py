from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
import time

class AllPortJoinAllVLANs(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	
    def __init__(self, *args, **kwargs):
        super(AllPortJoinAllVLANs , self).__init__(*args, **kwargs)

		
    def clearAllFlowsAndGroups(self, datapath):	
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
        #clear all flows
        match = parser.OFPMatch()
        self.del_flow(datapath , ofproto.OFPTT_ALL, 0, match, inst=[])
        #clear all groups
        buckets = []
        self.del_group(datapath, ofproto.OFPGT_INDIRECT, ofproto.OFPG_ALL, buckets)	
        time.sleep(10)

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

    def create_all_l2_interface(self, datapath, pvid=1, p_start=1, p_end=52, v_start=1, v_end=4093):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
        for v in range(v_start, v_end+1, 1):
            print "create %d vlan group"%v			
            for p in range(p_start, p_end+1, 1):
                group_id=(v<<16|p)
                if v==pvid:
                    actions = [parser.OFPActionOutput(port=p), parser.OFPActionPopVlan()]
                else:
                    actions = [parser.OFPActionOutput(port=p)]

                buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
                self.add_group(datapath, ofproto.OFPGT_INDIRECT, group_id, buckets)
            		
            #time.sleep(1)
        print "finish create l2_interface group"
				
    def create_all_port_join_all_vlan(self, datapath, pvid=1, p_start=1, p_end=52, v_start=1, v_end=4093):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
        for v in range(v_start, v_end+1, 1):
            print "create %d vlan flow"%v			
            for p in range(p_start, p_end+1, 1):
                actions = [parser.OFPActionSetField(vlan_vid=v)]
                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                        parser.OFPInstructionGotoTable(20)]
                match = parser.OFPMatch()
                if pvid == v:
                    match.set_vlan_vid_masked(0, 0x0fff)
                else:
                    match.set_vlan_vid_masked(v, 0x1fff)
					
                match.set_in_port(p)
                self.add_flow(datapath ,10 ,1, match , inst)	               

            #time.sleep(1)
						

        print "finish all port join all VLANs flows"
		

    def send_flow_stats_request(self, datapath):
        print "send flow stats request"
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        cookie = cookie_mask = 0
        #match = ofp_parser.OFPMatch(in_port=1)
        req = ofp_parser.OFPFlowStatsRequest(datapath=datapath, flags=0,
                                             table_id=ofp.OFPTT_ALL,
                                             out_port=ofp.OFPP_ANY, 
	                                         out_group=ofp.OFPG_ANY,
                                             cookie=cookie, cookie_mask=cookie_mask,
                                             match=None)
        datapath.send_msg(req)
				 
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
            print "flow stats reply handler"
            for stat in ev.msg.body:
                print('table_id=%s '
                             'duration_sec=%d duration_nsec=%d '
                             'priority=%d '
                             'idle_timeout=%d hard_timeout=%d flags=0x%04x '
                             'cookie=%d packet_count=%d byte_count=%d '
                             'match=%s instructions=%s\n' %
                             (stat.table_id,
                              stat.duration_sec, stat.duration_nsec,
                              stat.priority,
                              stat.idle_timeout, stat.hard_timeout, stat.flags,
                              stat.cookie, stat.packet_count, stat.byte_count,
                              stat.match, stat.instructions))		

    def send_group_stats_request(self, datapath):
        print "send group stats request"
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        req = ofp_parser.OFPGroupStatsRequest(datapath, 0, ofp.OFPG_ALL)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPGroupStatsReply, MAIN_DISPATCHER)
    def group_stats_reply_handler(self, ev):
        print "group stats reply handler"	
        for stat in ev.msg.body:
            print('length=%d group_id=%x '
                          'ref_count=%d packet_count=%d byte_count=%d '
                          'duration_sec=%d duration_nsec=%d\n' %
                          (stat.length, stat.group_id,
                           stat.ref_count, stat.packet_count,
                           stat.byte_count, stat.duration_sec,
                           stat.duration_nsec))
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
		
        self.clearAllFlowsAndGroups(datapath)
        start_port=1
        end_port=52
        start_vlan=1
        end_vlan=10 #4094 is reserved for management vlan
        default_vlan=1 # for untagged packet
        self.create_all_l2_interface(datapath, pvid=default_vlan, p_start=start_port, p_end=end_port, v_start=start_vlan, v_end=end_vlan)
        self.create_all_port_join_all_vlan(datapath, pvid=default_vlan, p_start=start_port, p_end=end_port, v_start=start_vlan, v_end=end_vlan)
        #get all flows to verify 
        self.send_flow_stats_request(datapath)
        #get all groups to verify 
        self.send_group_stats_request(datapath)
			
