from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER, DEAD_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu import utils
from ryu.lib import hub
import time

class StatsRequest(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	
    def __init__(self, *args, **kwargs):
        super(StatsRequest , self).__init__(*args, **kwargs)
        self.datapaths = {}        
        self.monitor_thread = hub.spawn(self._monitor)
        
    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self.send_port_stats_request(dp)
            hub.sleep(10)
        
    def clearAllFlowsAndGroups(self, datapath):	
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
        #clear all flows
        match = parser.OFPMatch()
        self.del_flow(datapath , ofproto.OFPTT_ALL, 0, match, inst=[])
        #clear all groups
        buckets = []
        self.del_group(datapath, ofproto.OFPGT_INDIRECT, ofproto.OFPG_ALL, buckets)	
        time.sleep(5)

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

        print "finish all port join all VLANs flows"

    @set_ev_cls(ofp_event.EventOFPPacketIn , MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        print "Packet in Event"		

    @set_ev_cls(ofp_event.EventOFPHello , MAIN_DISPATCHER)
    def hello_rx_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        print "Hello Rx Event"
		
    @set_ev_cls(ofp_event.EventOFPHello , DEAD_DISPATCHER)
    def hello_timeout_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        print "Hello Timeout Event"
		
    @set_ev_cls(ofp_event.EventOFPErrorMsg, [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg
        print "OFPErrorMsg received: type=0x%02x code=0x%02x 'message=%s'"%(msg.type, msg.code, utils.hex_array(msg.data))

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


    def send_port_stats_request(self, datapath):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        req = ofp_parser.OFPPortStatsRequest(datapath, 0, ofp.OFPP_ANY)
        datapath.send_msg(req)

		
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)		
    def port_stats_reply_handler(self, ev):
            for stat in ev.msg.body:
                if (stat.rx_packets!=0 or stat.tx_packets!=0) :
                    print('port_no=%d '
                             'rx_packets=%d tx_packets=%d '
                             'rx_bytes=%d tx_bytes=%d '
                             'rx_dropped=%d tx_dropped=%d '
                             'rx_errors=%d tx_errors=%d '
                             'rx_frame_err=%d rx_over_err=%d rx_crc_err=%d '
                             'collisions=%d duration_sec=%d duration_nsec=%d' %
                             (stat.port_no,
                              stat.rx_packets, stat.tx_packets,
                              stat.rx_bytes, stat.tx_bytes,
                              stat.rx_dropped, stat.tx_dropped,
                              stat.rx_errors, stat.tx_errors,
                              stat.rx_frame_err, stat.rx_over_err,
                              stat.rx_crc_err, stat.collisions,
                              stat.duration_sec, stat.duration_nsec))

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_handler(self, ev):
        print "state_change_handler"    
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                print('register datapath: %016x')%datapath.id
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                print('unregister datapath: %016x')%datapath.id
                del self.datapaths[datapath.id]


    def send_get_config_request(self, datapath):
        ofp_parser = datapath.ofproto_parser

        req = ofp_parser.OFPGetConfigRequest(datapath)
        datapath.send_msg(req)                
                
    @set_ev_cls(ofp_event.EventOFPGetConfigReply, MAIN_DISPATCHER)
    def get_config_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        flags = []

        if msg.flags & ofp.OFPC_FRAG_NORMAL:
            flags.append('NORMAL')
        if msg.flags & ofp.OFPC_FRAG_DROP:
            flags.append('DROP')
        if msg.flags & ofp.OFPC_FRAG_REASM:
            flags.append('REASM')
 
        print "flag %s"%flags
            
            
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath

        self.clearAllFlowsAndGroups(datapath)

        start_port=1
        end_port=3
        start_vlan=1
        end_vlan=2 #4094 is reserved for management vlan
        default_vlan=1 # for untagged packet
        #self.create_all_l2_interface(datapath, pvid=default_vlan, p_start=start_port, p_end=end_port, v_start=start_vlan, v_end=end_vlan)
        #self.create_all_port_join_all_vlan(datapath, pvid=default_vlan, p_start=start_port, p_end=end_port, v_start=start_vlan, v_end=end_vlan)

        self.send_get_config_request(datapath)
        #self.send_flow_stats_request(datapath)
        #self.send_group_stats_request(datapath)
        self.send_port_stats_request(datapath)
		