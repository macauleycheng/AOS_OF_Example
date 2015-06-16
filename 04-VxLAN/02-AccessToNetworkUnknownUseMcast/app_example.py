from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER, DEAD_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu import utils
from ryu.lib import mac
import edit_config	

SWITCH1="70:72:cf:dc:9e:da"
SWITCH2="70:72:cf:b5:ea:88"
SWITCH1_CONTROLLER="192.168.1.1"
SWITCH2_CONTROLLER="192.168.1.2"
PC1="00:00:11:22:33:44"
PC2="00:00:44:33:22:11"
VTEP_ID=0x10002
VTAP_ID=0x10001
VNI_ID=10

class appExample(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
   
    def __init__(self, *args, **kwargs):
        super(appExample , self).__init__(*args, **kwargs)
        self.datapaths = {}     

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
                
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        str_datapath_id_f= "{:016x}".format(datapath.id)        
        str_datapath_id=':'.join([str_datapath_id_f[i:i+2] for i in range(0, len(str_datapath_id_f), 2)])
        
        if str_datapath_id[6:] == SWITCH1:
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser        

            print "Set VxLAN config on %s, controller %s"%(SWITCH1, SWITCH1_CONTROLLER)
            edit_config.replace_vtep_vtap_nexthop("10.1.1.1", "10.1.2.1", SWITCH1, SWITCH2)
            edit_config.send_edit_config(SWITCH1_CONTROLLER, "netconfuser", "netconfuser")

            print "Add group for VTEP output port/vlan, 0x0002(vlan) 0002(port)"
            #although it is very strange to add group only, but it need for chip problem.
            #because the output port don't join vlan 2 will be dropped.
            actions = [parser.OFPActionOutput(2) ]
            buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
            self.add_group(datapath, ofproto.OFPGT_INDIRECT, 0x00020002, buckets)
      
            print "Add Flow table 0"
            inst = [parser.OFPInstructionGotoTable(50)]
            match = parser.OFPMatch()
            match.set_in_port(0x10000)
            self.add_flow(datapath ,0 ,1, match , inst)        
       
            print "Add Flow table 50"
            actions = [parser.OFPActionOutput(VTEP_ID)]        
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()
            match.set_tunnel_id(VNI_ID)
            match.set_dl_dst(mac.haddr_to_bin(PC2))
            self.add_flow(datapath ,50 ,1, match , inst)        
            
            actions = [parser.OFPActionOutput(VTAP_ID)]        
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()
            match.set_tunnel_id(VNI_ID)
            match.set_dl_dst(mac.haddr_to_bin(PC1))
            self.add_flow(datapath ,50 ,1, match , inst)        

        elif str_datapath_id[6:] == SWITCH2:
            print "Set VxLAN config on %s, controller %s"%(SWITCH2, SWITCH2_CONTROLLER)        
            edit_config.replace_vtep_vtap_nexthop("10.1.2.1", "10.1.1.1", SWITCH2, SWITCH1)
            edit_config.send_edit_config(SWITCH2_CONTROLLER, "netconfuser", "netconfuser")

            print "Add Flow table 0"
            inst = [parser.OFPInstructionGotoTable(50)]
            match = parser.OFPMatch()
            match.set_in_port(0x10000)

            self.add_flow(datapath ,0 ,1, match , inst)   
            print "Add group for VTEP output port/vlan, 0x0001(vlan) 0002(port)"
            actions = [parser.OFPActionOutput(2) ]
            buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
            self.add_group(datapath, ofproto.OFPGT_INDIRECT, 0x00010002, buckets)

            print "Add Flow table 50"
            actions = [parser.OFPActionOutput(VTEP_ID)]        
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()
            match.set_vlan_vid(VNI_ID)
            match.set_dl_dst(mac.haddr_to_bin(PC2))
            self.add_flow(datapath ,50 ,1, match , inst)        
            
            actions = [parser.OFPActionOutput(VTAP_ID)]        
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()
            match.set_vlan_vid(VNI_ID)
            match.set_dl_dst(mac.haddr_to_bin(PC1))
            self.add_flow(datapath ,50 ,1, match , inst)            
        
        else:
            print "Can't find SWITCH"

    def add_flow(self, datapath , table_id, priority , match , inst):
       ofproto = datapath.ofproto
       parser = datapath.ofproto_parser
       mod = parser.OFPFlowMod(datapath=datapath, table_id=table_id, priority=priority ,
                               match=match , instructions=inst)
       datapath.send_msg(mod)

    def add_group(self, datapath, type, group_id, buckets):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
        req = parser.OFPGroupMod(datapath, ofproto.OFPGC_ADD,
                                 type, group_id, buckets)
        datapath.send_msg(req)	
        
