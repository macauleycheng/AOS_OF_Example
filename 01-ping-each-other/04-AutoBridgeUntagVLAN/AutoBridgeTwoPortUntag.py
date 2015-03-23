from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import vlan
from ryu.lib import mac
from accton_api.bridge_util import bridge_util
from accton_api.vlan_util import vlan_util
from accton_api.msg_util import msg_util

class AutoBridgeTwoPortUntag(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	
    def __init__(self, *args, **kwargs):
        super(AutoBridgeTwoPortUntag , self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapath_set=None

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapath_set=datapath

        msg_util.clearAllFlowsAndGroups(datapath)
		
        self.addDefaultGroupFlows(datapath)
		
    def addDefaultGroupFlows(self, datapath):	
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser	
        
        #ARP/ARP-reply goto controller BY ACL
        match = parser.OFPMatch(eth_type=0x0806)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        msg_util.add_flow(datapath , 60, 1, match , inst)
	
    @set_ev_cls(ofp_event.EventOFPPacketIn , MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        print("packet in %s %s %s %s")%(dpid, src, dst, in_port)
		
        # learn a mac address to avoid FLOOD next time.
        if src not in self.mac_to_port[dpid]:
            bridge_util.add_client(datapath, 1, src, in_port, False)

        self.mac_to_port[dpid][src] = in_port

        #packet-out for DLF
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
            print "out_port %d"%out_port
        else:
            out_port = ofproto.OFPP_FLOOD
            print "out_port Flood"

        data = msg.data

        msg_util.packet_out(datapath, out_port, msg.data)
