from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import mac
from ryu import utils
import edit_config

class app_example(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	
    def __init__(self, *args, **kwargs):
        super( app_example, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto		
        parser = datapath.ofproto_parser			
        self.clearAllFlowsAndGroups(datapath)
        
        print "Set VxLAN config"
        edit_config.replace_vtep_vtap_nexthop("10.1.1.1", "10.1.2.1", "70:72:cf:dc:9e:da", "70:72:cf:b5:ea:88")
        edit_config.send_edit_config("192.168.1.1", "netconfuser", "netconfuser")

        print "Start to add L2 overlay Flood Group"
        #create L2_Overlay_Flood_Group
        #group_id=([9:0}index, [11:10]subtgype, [27:12]TunnelId, [31:28]:8
        #VTEP port used phy port shall not the same as "of-agent vni 10 multicast 224.1.1.1 nexthop 20"
        #used phy_port or output port packet will be multicast packet
        action_vtep = [parser.OFPActionOutput(port=0x10001)]
        action_vtap = [parser.OFPActionOutput(port=0x10002)]
        buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=action_vtep),
                   parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=action_vtap)]
        self.add_group(datapath, ofproto.OFPGT_ALL, 0x8000a001, buckets)
        print "Finish adding L2 Overlay Flood Group"        

        print "Add Flow table 0, just add this flow"
        inst = [parser.OFPInstructionGotoTable(50)]
        match = parser.OFPMatch()
        match.set_in_port(0x10000)
        self.add_flow(datapath ,0 ,1, match , inst)   		
        
        print "add Bridge Flow"
        #add bridge flow        
        actions = [parser.OFPActionGroup(0x8000a001)]        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                parser.OFPInstructionGotoTable(60)]
        match = parser.OFPMatch()
        #on edit_config we use VNI 10
        match.set_tunnel_id(10) 
        self.add_flow(datapath ,50 ,1, match , inst)        
        
    @set_ev_cls(ofp_event.EventOFPPacketIn , MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

    @set_ev_cls(ofp_event.EventOFPErrorMsg, [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg
        print "OFPErrorMsg received: type=0x%02x code=0x%02x 'message=%s'"%(msg.type, msg.code, utils.hex_array(msg.data))

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
