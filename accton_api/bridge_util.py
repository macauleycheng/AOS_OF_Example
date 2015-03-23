from sets import Set
from accton_api.vlan_util import vlan_util
from accton_api.msg_util import msg_util

class bridge_util():

    def __init__(self, *args, **kwargs):
        super(bridge_util , self).__init__(*args, **kwargs)
	
    #type:31-28, vlan_id:27-16, id use vlan_id
    @staticmethod	
    def encode_group_dlf(vlan_id):
        group_id = 0x40000000 | vlan_id<<16 | vlan_id
        return group_id
	
    @staticmethod	
    def add_client(datapath, vlan_id, mac_addr, port, is_tag):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser	
        #add egress group
        #print "add client %d, %d %d, %s"%(vlan_id, is_tag, port, mac_addr)
        l2_intf_group_id=vlan_util.add_port_egress_group(datapath, vlan_id, is_tag, port)        
		
        #add vlan table flow to rx packet, BCM bug? if add untag, shall add rx tag, too.
        vlan_util.add_port_ingress_vlan_flow(datapath, vlan_id, True, port)		
        if is_tag == False:
            vlan_util.add_port_ingress_vlan_flow(datapath, vlan_id, False, port)			

        #add bridge flow
        actions = [parser.OFPActionGroup(l2_intf_group_id)]       
        match = parser.OFPMatch(vlan_vid=vlan_id, eth_dst=mac_addr)
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                parser.OFPInstructionGotoTable(60)]
        msg_util.add_flow(datapath ,50 ,1, match , inst)
	
    @staticmethod	
    def create_dlf_group(datapath, vlan_id, port_list):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser	
        groups=Set()
        for port in port_list:
            #collect group_id
            groups.add(vlan_util.add_port_egress_group(datapath, vlan_id, False, port))

        bucket_actions=[]
        for group_id in groups:
            bucket_actions.append(parser.OFPActionGroup(group_id))

        buckets=[]
        for bk_action in bucket_actions:
            buckets.append( parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=bk_action) )

        dlf_group_id = bridge_util.encode_group_dlf(vlan_id)			
        msg_util.add_group(datapath, ofproto.OFPGT_ALL, dlf_group_id, buckets)
        return dlf_group_id
	
    @staticmethod
    def create_dlf_flow(datapath, vlan_id, to_controller, dlf_group_id):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
		
        match = parser.OFPMatch()
        match.set_vlan_vid(vlan_id)
        if to_controller:
            actions_c = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
			
        actions_g = [parser.OFPActionGroup(dlf_group_id)]

        if to_controller:
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions_c),
		            parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions_g),
                    parser.OFPInstructionGotoTable(60)]
        else:
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions_g),
                    parser.OFPInstructionGotoTable(60)]

        msg_util.add_flow(datapath , 50, 1, match, inst)	