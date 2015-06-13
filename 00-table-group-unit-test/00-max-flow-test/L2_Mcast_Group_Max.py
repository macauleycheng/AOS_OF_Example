from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
import time

max_entry_num=16384
max_port_id=52
max_vlan_id=4093
l2_mcast_group_curr_num=0
sleep_time=1

class L2McastGroupMaxTest(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L2McastGroupMaxTest , self).__init__(*args, **kwargs)


    def clearAllFlowsAndGroups(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        #clear all flows
        match = parser.OFPMatch()
        self.del_flow(datapath , ofproto.OFPTT_ALL, 0, match, inst=[])
        #clear all groups
        buckets = []
        self.del_group(datapath, ofproto.OFPGT_INDIRECT, ofproto.OFPG_ALL, buckets)
        time.sleep(sleep_time)

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

    def create_all_l2_interface(self, datapath, pvid, p_start, p_end, v_start, v_end):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        for v in range(v_start, v_end+1, 1):
            print "create all L2 intf groups in VLAN %d" % v
            for p in range(p_start, p_end+1, 1):
                group_id=(v<<16|p)
                if v==pvid:
                    actions = [parser.OFPActionOutput(port=p), parser.OFPActionPopVlan()]
                else:
                    actions = [parser.OFPActionOutput(port=p)]

                buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
                self.add_group(datapath, ofproto.OFPGT_INDIRECT, group_id, buckets)
                time.sleep(sleep_time)
        print "finish create l2_interface group"


    # ./dpctl tcp:192.168.1.10:6633 group-mod cmd=add,type=all,group=0x30020001
    # group=any,port=any,weight=1 group=0x20001 group=any,port=any,weight=1
    # group=0x20003 group=any,port=any,weight=1 group=0x20005
    def create_all_l2_mcast_group(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        print 'Start to test l2 multicast group'
        for i in range(1, (max_entry_num / max_vlan_id) + 1, 1):
            for v in range(1, max_vlan_id+1, 1):
                #print 'create L2 multicast group in VLAN %d' % v
                buckets = []
                for p in range(1, max_port_id+1, 1):
                    #create l2_mcast_group, type is all
                    actions = [parser.OFPActionGroup((v <<16) + p)]
                    buckets.append(parser.OFPBucket(weight=100, watch_port=ofproto.OFPP_ANY, watch_group=ofproto.OFPG_ANY, actions=actions))
                #print buckets
                self.add_group(datapath, ofproto.OFPGT_ALL, (0x30000000 + (v<<16) + i), buckets)
                #print 'Finish to create L2 multicast group %x' % (0x30000000 + (v<<16) + i)
                time.sleep(sleep_time)
        print 'Finish to full l2 multicast group testing'

    def send_group_stats_request(self, datapath):
        print "send group stats request"
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        req = ofp_parser.OFPGroupStatsRequest(datapath, 0, ofp.OFPG_ALL)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPGroupStatsReply, MAIN_DISPATCHER)
    def group_stats_reply_handler(self, ev):
        global l2_mcast_group_curr_num
        print 'group stats reply handler'
        for stat in ev.msg.body:
            #print('length=%d group_id=%x '
            #              'ref_count=%d packet_count=%d byte_count=%d '
            #              'duration_sec=%d duration_nsec=%d\n' %
            #              (stat.length, stat.group_id,
            #               stat.ref_count, stat.packet_count,
            #               stat.byte_count, stat.duration_sec,
            #               stat.duration_nsec))
            if ((stat.group_id & 0x30000000) != 0):
                l2_mcast_group_curr_num += 1;

        if (l2_mcast_group_curr_num != max_entry_num):
            print ('Get group stats reply, not reach max L2 multicast group yet, current entry is %d, max is %d' % (l2_mcast_group_curr_num, max_entry_num))
        else:
            print ('Get group stats reply, success to reach max L2 multicast group, current entry is %d, max is %d' % (l2_mcast_group_curr_num, max_entry_num))


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.clearAllFlowsAndGroups(datapath)
        self.create_all_l2_interface(datapath, pvid=0, p_start=1, p_end=max_port_id, v_start=1, v_end=max_vlan_id)
        self.create_all_l2_mcast_group(datapath)
        #get all groups to verify
        self.send_group_stats_request(datapath)

