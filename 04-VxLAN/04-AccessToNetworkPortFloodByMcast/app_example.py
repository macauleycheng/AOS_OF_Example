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
VTEP_PHY_PORT=2
VTEP_VLAN=2
VTAP_PHY_PORT=1

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
            #For VTEP ouput
            actions = [parser.OFPActionOutput(VTEP_PHY_PORT) ]
            buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
            self.add_group(datapath, ofproto.OFPGT_INDIRECT, 0x00020002, buckets)

            print "Add Flow table 0"
            inst = [parser.OFPInstructionGotoTable(50)]
            match = parser.OFPMatch()
            match.set_in_port(0x10000)
            self.add_flow(datapath ,0 ,1, match , inst)        

            print "Add Flow table 50"
            #For VTAP -> VTEP
            actions = [parser.OFPActionOutput(VTEP_ID)]        
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()
            match.set_tunnel_id(VNI_ID)
            match.set_dl_dst(mac.haddr_to_bin(PC2))
            self.add_flow(datapath ,50 ,1, match , inst)        
            #For VTEP -> VTAP
            actions = [parser.OFPActionOutput(VTAP_ID)]        
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()
            match.set_tunnel_id(VNI_ID)
            match.set_dl_dst(mac.haddr_to_bin(PC1))
            self.add_flow(datapath ,50 ,1, match , inst)        
            #for VTAP add vlan flow table and termination flow table
            #The reason to add below two flows is that CHIP need to known the DA  need terminate here
            #VLAN flow for passing vlan checking, termination flow for vxlan packet termination
            actions = [parser.OFPActionSetField(vlan_vid=VTEP_VLAN)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(20)]
            match = parser.OFPMatch()
            match.set_vlan_vid_masked(VTEP_VLAN, 0x1fff)
            match.set_in_port(VTEP_PHY_PORT)
            self.add_flow(datapath ,10 ,1, match , inst)       
            #add termination flow
            inst = [parser.OFPInstructionGotoTable(30)]
            match = parser.OFPMatch()
            match.set_vlan_vid(VTEP_VLAN)
            match.set_in_port(VTEP_PHY_PORT)
            match.set_dl_type(0x0800)
            match.set_dl_dst(mac.haddr_to_bin(SWITCH1))
            self.add_flow(datapath ,20 ,1, match , inst)               
            
            #To process the packet DA rx on VTAP which is still not write on Brige Flow table,
            #We need to add a uknonw flow group to handl this
            #create L2_Overlay_Flood_Group
            #group_id=([9:0}index, [11:10]subtgype, [27:12]TunnelId, [31:28]:8
            #VTEP port used phy port shall not the same as "of-agent vni 10 multicast 224.1.1.1 nexthop 20" used phy_port
            l2_overlay_flood_group_id=0x80000401 | VNI_ID<<12
            #note: It will be ok to use "l2_overlay_flood_group_id=0x80000001 | VNI_ID<<12"
            print "l2_overlay_flood_group_id is %lx"%l2_overlay_flood_group_id
            action_vtep = [parser.OFPActionOutput(port=0x10001)]
            buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=action_vtep)]
            self.add_group(datapath, ofproto.OFPGT_ALL, l2_overlay_flood_group_id, buckets)
            #add bridge flow        
            actions = [parser.OFPActionGroup(l2_overlay_flood_group_id)]        
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()            
            match.set_tunnel_id(VNI_ID) 
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
            actions = [parser.OFPActionOutput(VTEP_PHY_PORT) ]
            buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
            self.add_group(datapath, ofproto.OFPGT_INDIRECT, 0x00010002, buckets)

            print "Add Flow table 50"
            #For VTAP -> VTEP            
            actions = [parser.OFPActionOutput(VTEP_ID)]        
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()
            match.set_vlan_vid(VNI_ID)
            match.set_dl_dst(mac.haddr_to_bin(PC2))
            self.add_flow(datapath ,50 ,1, match , inst)        
            #For VTEP -> VTAP            
            actions = [parser.OFPActionOutput(VTAP_ID)]        
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()
            match.set_vlan_vid(VNI_ID)
            match.set_dl_dst(mac.haddr_to_bin(PC1))
            self.add_flow(datapath ,50 ,1, match , inst)            
            #for VTAP add vlan flow table and termination flow table
            #The reason to add below two flows is that CHIP need to known the DA  need terminate here
            #VLAN flow for passing vlan checking, termination flow for vxlan packet termination
            actions = [parser.OFPActionSetField(vlan_vid=VTEP_VLAN)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(20)]
            match = parser.OFPMatch()
            match.set_vlan_vid_masked(VTEP_VLAN, 0x1fff)
            match.set_in_port(VTEP_PHY_PORT)
            self.add_flow(datapath ,10 ,1, match , inst)       
            #add termination flow
            inst = [parser.OFPInstructionGotoTable(30)]
            match = parser.OFPMatch()
            match.set_vlan_vid(VTEP_VLAN)
            match.set_in_port(VTEP_PHY_PORT)
            match.set_dl_type(0x0800)
            match.set_dl_dst(mac.haddr_to_bin(SWITCH2))
            self.add_flow(datapath ,20 ,1, match , inst)    
            
            #To process the packet DA rx on VTAP which is still not write on Brige Flow table,
            #We need to add a uknonw flow group to handl this
            #create L2_Overlay_Flood_Group
            #group_id=([9:0}index, [11:10]subtgype, [27:12]TunnelId, [31:28]:8
            #VTEP port used phy port shall not the same as "of-agent vni 10 multicast 224.1.1.1 nexthop 20" used phy_port
            l2_overlay_flood_group_id=0x80000001 | VNI_ID<<12
            print "l2_overlay_flood_group_id is %lx"%l2_overlay_flood_group_id
            action_vtep = [parser.OFPActionOutput(port=0x10001)]
            buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=action_vtep)]
            self.add_group(datapath, ofproto.OFPGT_ALL, l2_overlay_flood_group_id, buckets)
            #add bridge flow        
            actions = [parser.OFPActionGroup(l2_overlay_flood_group_id)]        
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()            
            match.set_tunnel_id(VNI_ID) 
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
        
