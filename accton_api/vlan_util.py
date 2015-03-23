
from accton_api.msg_util import msg_util

class vlan_util():

    def __init__(self, *args, **kwargs):
        super(vlan_util , self).__init__(*args, **kwargs)

    #type:31-28, vlan_id:27-16, tag/untag:15, port 14-0
	#tag/untag is by myself define
    @staticmethod	
    def encode_group_l2_intf(vlan_id, is_tag, port_id):
        group_id=(vlan_id<<16|port_id)
        if is_tag:
            group_id = group_id | 1<<15
        #print "encode_group_l2_intf %d"%group_id
        return group_id

    @staticmethod
    def add_port_egress_group(datapath, vlan_id, is_tag, port_id):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
		
        if is_tag:
            actions = [parser.OFPActionOutput(port=port_id)]
        else:
            actions = [parser.OFPActionOutput(port=port_id), parser.OFPActionPopVlan()]
      
        buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
        group_id=vlan_util.encode_group_l2_intf(vlan_id, is_tag, port_id)
        msg_util.add_group(datapath, ofproto.OFPGT_INDIRECT, group_id, buckets)
        return group_id

    @staticmethod		
    def add_port_ingress_vlan_flow(datapath, vlan_id, is_tag, port_id):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
		
        actions = [parser.OFPActionSetField(vlan_vid=vlan_id)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                parser.OFPInstructionGotoTable(20)]
        match = parser.OFPMatch()
        if is_tag:
            match.set_vlan_vid_masked(vlan_id, 0x1fff)
        else:
            match.set_vlan_vid_masked(0, 0x0fff)

        match.set_in_port(port_id)
        msg_util.add_flow(datapath ,10 ,1, match , inst)	
		
		