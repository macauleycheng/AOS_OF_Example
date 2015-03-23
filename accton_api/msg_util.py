


class msg_util():

    def __init__(self, *args, **kwargs):
        super(msg_util , self).__init__(*args, **kwargs)
		
    @staticmethod
    def add_group(datapath, type, group_id, buckets):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
        req = parser.OFPGroupMod(datapath, ofproto.OFPGC_ADD,
                                 type, group_id, buckets)
        #print "add_group %d, %s"%(group_id, buckets)
        datapath.send_msg(req)		

    @staticmethod
    def del_group(datapath, type, group_id, buckets):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
        req = parser.OFPGroupMod(datapath, ofproto.OFPGC_DELETE,
                                 type, group_id, buckets)
        datapath.send_msg(req)	

    @staticmethod		
    def add_flow(datapath , table_id, priority , match , inst):
       ofproto = datapath.ofproto
       parser = datapath.ofproto_parser
       mod = parser.OFPFlowMod(datapath=datapath, table_id=table_id, priority=priority ,
                               match=match , instructions=inst)
       #print "add_flow %d, match %s, inst %s"%(table_id, match, inst)
       datapath.send_msg(mod)
	   
    @staticmethod
    def del_flow(datapath , table_id, priority , match , inst):
       ofproto = datapath.ofproto
       parser = datapath.ofproto_parser
       mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE, table_id=table_id, priority=priority,
	                           out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                               match=match , instructions=inst)
       datapath.send_msg(mod)

    @staticmethod
    def packet_out(datapath, out_port, data): 
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        actions = [parser.OFPActionOutput(out_port)]
        out = parser.OFPPacketOut(datapath=datapath , 
                                  buffer_id=ofproto.OFP_NO_BUFFER ,
                                  in_port=ofproto.OFPP_CONTROLLER , 
                                  actions=actions , data=data)
        datapath.send_msg(out)
	   
    @staticmethod
    def clearAllFlowsAndGroups(datapath):	
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser		
        #clear all flows
        match = parser.OFPMatch()
        msg_util.del_flow(datapath , ofproto.OFPTT_ALL, 0, match, inst=[])
        #clear all groups
        buckets = []
        msg_util.del_group(datapath, ofproto.OFPGT_INDIRECT, ofproto.OFPG_ALL, buckets)		   
	   
	   