from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
import time

l3_ucast_group_curr_num=0
net_route_v6_start=[0x2000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000]
net_route_v6_mask=[0xffff, 0xffff, 0xffff, 0xffff, 0xffff, 0xffff, 0xffff, 0x0000]
net_route_v6_num_max=8192/2

host_route_v6_start=[0x2000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0001]
host_route_v6_mask=[0xffff, 0xffff, 0xffff, 0xffff, 0xffff, 0xffff, 0xffff, 0xffff]
host_route_v6_num_max=147456/2
host_route_collision_retry_time=500000
sleep_time=1


def change_mac(mac, offset):
    new_mac="{:012X}".format(int(mac, 16) + offset)
    return ':'.join([new_mac[i:i+2] for i in range(0, len(new_mac), 2)])

class UcastRouteV6FlowMaxTest(app_manager.RyuApp):

    _CONTEXTS = {'dpset': dpset.DPSet}
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(UcastRouteV6FlowMaxTest , self).__init__(*args, **kwargs)


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

    # ./dpctl tcp:192.168.1.10:6633 flow-mod table=30,cmd=add,prio=301
    # eth_type=0x000086dd,ipv6_dst=2014::1/64 write:group=0x20000001 goto:60
    def create_max_ucast_route_v6_flow(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # create l2 intf group
        actions = [parser.OFPActionOutput(port=1)]
        buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
        self.add_group(datapath, ofproto.OFPGT_INDIRECT, 0x10001, buckets)

        # create l3 ucast group
        actions = [parser.OFPActionSetField(vlan_vid=1),parser.OFPActionSetField(eth_dst="000000000001"),
                   parser.OFPActionSetField(eth_src="200000000001"), parser.OFPActionGroup(0x10001)]
        buckets = [parser.OFPBucket(weight=100, watch_port=0, watch_group=0, actions=actions)]
        self.add_group(datapath, ofproto.OFPGT_INDIRECT, (0x20010001), buckets)

        # create net route
        print 'Start to test full net route flow'
        actions = [parser.OFPActionGroup(0x20010001)]
        route_start = list(net_route_v6_start)
        for i in range(0, net_route_v6_num_max, 1):
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()
            match.set_dl_type(0x86dd)
            match.set_ipv6_dst_masked(route_start, net_route_v6_mask)
            self.add_flow(datapath ,30 ,1, match , inst)
            #print 'i=%d, net_route_v6_num_max=%d, route_start[%d]=%x' % (i, net_route_v6_num_max, i/0xffff, route_start[i/0xffff])
            route_start[i/0xffff] += 1
            #print 'i=%d, net_route_v6_num_max=%d, route_start[%d]=%x' % (i, net_route_v6_num_max, i/0xffff, route_start[i/0xffff])
            time.sleep(sleep_time)

        # create host route
        print 'Start to test full host route flow'
        route_start = list(host_route_v6_start)
        for i in range(0, host_route_v6_num_max + host_route_collision_retry_time, 1):
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(60)]
            match = parser.OFPMatch()
            match.set_dl_type(0x86dd)
            match.set_ipv6_dst_masked(route_start, host_route_v6_mask)
            self.add_flow(datapath ,30 ,1, match , inst)
            route_start[i/0xffff] += 1
            time.sleep(sleep_time)

        print 'Finish to unicst route full flow testing'

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
            if(stat.table_id == 30):
                if(stat.active_count != (net_route_v6_num_max + host_route_v6_num_max)):
                    print "Failed!! current entry count is %d" % stat.active_count
                else:
                    print "Success!! current entry count is %d" % stat.active_count

        print ('TableStats: ', tables)

    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def handler_datapath(self, ev):
        print "=Event DP="
        print "dpid: %i" % ev.dp.id
        if ev.enter:
            self.clearAllFlowsAndGroups(ev.dp)
            self.create_max_ucast_route_v6_flow(ev.dp)
            self.send_table_stats_request(ev.dp)