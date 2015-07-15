from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import mac
import time
import ipaddr

match_ip_start=ipaddr.IPAddress('2.0.0.1')
match_ipv6_start=[0x2000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0001]
v4_entry_num=1286
v6_entry_num=1286
sleep_time=0.1

def change_mac(mac, offset):
    new_mac="{:012X}".format(int(mac, 16) + offset)
    return ':'.join([new_mac[i:i+2] for i in range(0, len(new_mac), 2)])

class PolicAclFlowMaxTest(app_manager.RyuApp):

    _CONTEXTS = {'dpset': dpset.DPSet}
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PolicAclFlowMaxTest , self).__init__(*args, **kwargs)


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


    # ./dpctl tcp:192.168.1.10:6633 flow-mod table=50,cmd=add,prio=301
    # eth_dst=00:00:00:22:44:77,vlan_vid=2 write:group=0x20003 goto:60
    def create_max_policy_acl_flow(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # create l2 intf group
        print "create all L2 intf group"
        l2_intf_group_id=0x20001
        actions = [parser.OFPActionOutput(port=1)]
        buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
        self.add_group(datapath, ofproto.OFPGT_INDIRECT, l2_intf_group_id, buckets)
        time.sleep(sleep_time)
        print "finish create L2 intf group"

        # create full ucast bridge flow
        print 'Start to test full policy acl flow'
        for i in range(0, v6_entry_num, 1):
            actions = [parser.OFPActionGroup(l2_intf_group_id)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions)]
            match = parser.OFPMatch()
            match.set_dl_type(0x86dd)
            match.set_ipv6_dst(match_ipv6_start)
            self.add_flow(datapath ,60 ,1, match , inst)
            time.sleep(sleep_time)
            match_ipv6_start[7] += 1

        for i in range(0, v6_entry_num, 1):
            actions = [parser.OFPActionGroup(l2_intf_group_id)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions)]
            match = parser.OFPMatch()
            match.set_dl_type(0x86dd)
            match.set_ipv6_src(match_ipv6_start)
            self.add_flow(datapath ,60 ,1, match , inst)
            time.sleep(sleep_time)
            match_ipv6_start[7] += 1

        for i in range(0, v4_entry_num, 1):
            actions = [parser.OFPActionGroup(l2_intf_group_id)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions)]
            match = parser.OFPMatch()
            match.set_dl_type(0x0800)
            match.set_ipv4_dst( (match_ip_start + i))
            self.add_flow(datapath ,60 ,1, match , inst)
            time.sleep(sleep_time)

        print 'Finish to full policy acl flow testing'


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

    def send_table_stats_request(self, datapath):
        print "send table stats request"
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        req = ofp_parser.OFPTableStatsRequest(datapath, ofp.OFPMPF_REQ_MORE)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPTableStatsReply, MAIN_DISPATCHER)
    def table_stats_reply_handler(self, ev):
        tables = []
        for stat in ev.msg.body:
            tables.append('table_id=%d active_count=%d lookup_count=%d '
                          ' matched_count=%d' %
                          (stat.table_id, stat.active_count,
                           stat.lookup_count, stat.matched_count))
            if(stat.table_id == 60):
                if(stat.active_count != (v4_entry_num + v6_entry_num)):
                    print "Failed !!"
                else:
                    print "Success!!"

        print ('TableStats: ', tables)


    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def handler_datapath(self, ev):
        print "=Event DP="
        print "dpid: %i" % ev.dp.id
        if ev.enter:
            self.clearAllFlowsAndGroups(ev.dp)
            self.create_max_policy_acl_flow(ev.dp)
            self.send_table_stats_request(ev.dp)
