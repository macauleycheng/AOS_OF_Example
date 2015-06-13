from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
import time

da_start="000000000001"
sa_start="200000000001"
entry_num=49150
max_vlan_id=4092
l3_ucast_group_curr_num=0
sleep_time=1


def change_mac(mac, offset):
    new_mac="{:012X}".format(int(mac, 16) + offset)
    return ':'.join([new_mac[i:i+2] for i in range(0, len(new_mac), 2)])

class L3UcastGroupMaxTest(app_manager.RyuApp):

    _CONTEXTS = {'dpset': dpset.DPSet}
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L3UcastGroupMaxTest , self).__init__(*args, **kwargs)


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

    # ./dpctl tcp:192.168.1.10:6633 group-mod cmd=add,type=ind,group=0x20000001
    #  group=any,port=any,weight=1 set_field=eth_src=00:00:09:00:00:00,
    #  set_field=eth_dst=00:00:09:00:01:00,set_field=vlan_vid=3,group=0x30003
    #
    def create_max_l3_ucast_group(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # create l2 intf group
        for v in range(1, max_vlan_id+1, 1):
            print "create L2 intf groups in VLAN %d" % v
            group_id=(v<<16) + 1
            actions = [parser.OFPActionOutput(port=1)]
            buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
            self.add_group(datapath, ofproto.OFPGT_INDIRECT, group_id, buckets)
            time.sleep(sleep_time)
        print "finish create l2_interface group"

        # create l3 ucast group
        for i in range(1, entry_num+1, 1):
            v = (i % max_vlan_id) + 1
            #create l3_unicast_group, type is indirect, vlan_vid shall be l2_interface_group vid
            actions = [parser.OFPActionSetField(vlan_vid=v),parser.OFPActionSetField(eth_dst=change_mac(da_start, i)),
                       parser.OFPActionSetField(eth_src=sa_start), parser.OFPActionGroup((v <<16) + 1)]
            buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
            self.add_group(datapath, ofproto.OFPGT_INDIRECT, (0x20000000 + (v<<16) + ((i/max_vlan_id)+1) ), buckets)
            time.sleep(1)

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
        global l3_ucast_group_curr_num
        print 'group stats reply handler'
        print('l3_ucast_group_curr_num is %d' % l3_ucast_group_curr_num)
        for stat in ev.msg.body:
            #print('length=%d group_id=%x '
            #              'ref_count=%d packet_count=%d byte_count=%d '
            #              'duration_sec=%d duration_nsec=%d\n' %
            #              (stat.length, stat.group_id,
            #               stat.ref_count, stat.packet_count,
            #               stat.byte_count, stat.duration_sec,
            #               stat.duration_nsec))
            if ((stat.group_id & 0x20000000) == 0x20000000):
                l3_ucast_group_curr_num += 1;

        if (l3_ucast_group_curr_num != entry_num):
            print ('Get group stats reply, not reach max L3 unicast group yet, current entry is %d, max is %d' % (l3_ucast_group_curr_num, entry_num))
        else:
            print ('Get group stats reply, success to test max L3 unicast group, current entry is %d, max is %d' % (l3_ucast_group_curr_num, entry_num))


    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def handler_datapath(self, ev):
        print "=Event DP="
        print "dpid: %i" % ev.dp.id
        if ev.enter:
            self.clearAllFlowsAndGroups(ev.dp)
            self.create_max_l3_ucast_group(ev.dp)
            self.send_group_stats_request(ev.dp)