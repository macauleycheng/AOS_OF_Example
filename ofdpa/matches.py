#*********************************************************************
#
# (C) Copyright Broadcom Corporation 2013-2014
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#*********************************************************************

#
# Implements Matches object
#

from ryu.lib import mac
from ofdpa.utils import Utils

class Matches():

    def __init__(self, *args, **kwargs):
        super(Matches, self).__init__(*args, **kwargs)

    @staticmethod
    def create_matches(dp, config):
        #
        #TODO: vlan mask
        matches = dp.ofproto_parser.OFPMatch()
        #
        # matches config is a list
        print "matches config: %s" % config
        #
        for key in config.keys():
            #
            #print "key: %s" % key
            #print "val: %s" % config[key]
            #
            if key[0] == '#':
                continue

            val = config[key]
            #
            if (key == "in_port"):
                matches.set_in_port(int(val))

            elif (key == "in_phy_port"):
                matches.set_in_phy_port(int(val))

            elif (key == "metadata"):
                matches.set_metadata(int(val))

            elif (key == "eth_dst"):
                matches.set_dl_dst(mac.haddr_to_bin(val))

            elif (key == "eth_dst_mask"):
                haddr = mac.haddr_to_bin(config["eth_dst"])
                mask = mac.haddr_to_bin(val)
                matches.set_dl_dst_masked(haddr,mask)

            elif (key == "eth_src"):
                matches.set_dl_src(mac.haddr_to_bin(val))

            elif (key == "eth_src_mask"):
                haddr = mac.haddr_to_bin(config["eth_src"])
                mask = mac.haddr_to_bin(val)
                matches.set_dl_src_masked(mac,mask)

            elif (key == "eth_type"):
                matches.set_dl_type(int(val,16))

            elif (key == "vlan_vid"):
                lst = val.split(',')
                if(len(lst) == 1):
                    vlan_vid = Utils.to_int(lst[0])
                    if (vlan_vid == 0):
                        matches.set_vlan_vid_none()
                    else:
                        matches.set_vlan_vid(vlan_vid)
                elif(len(lst) == 2):
                    vlan_vid = Utils.to_int(lst[0])
                    vlan_vid_mask = Utils.to_int(lst[1])
                    matches.set_vlan_vid_masked(vlan_vid, vlan_vid_mask)
                else:
                    print key, ": only two values allowed, key ignored"

            elif (key == "vlan_pcp"):
                matches.set_vlan_pcp(int(val))

            elif (key == "ip_dscp"):
                matches.set_ip_dscp(int(val))

            elif (key == "ip_ecn"):
                raise Exception("Wrong match name:", key)

            elif (key == "ip_proto"):
                matches.set_ip_proto(int(val))

            elif (key == "ipv4_src"):
                matches.set_ipv4_src(Matches.ipv4_to_int(val))

            elif (key == "ipv4_src_mask"):
                addr = Matches.ipv4_to_int(config["ipv4_src"])
                mask = Matches.mask_ntob(int(val))
                #mask = Matches.ipv4_to_int(val)
                matches.set_ipv4_src_masked(addr, mask)

            elif (key == "ipv4_dst"):
                matches.set_ipv4_dst(Matches.ipv4_to_int(val))

            elif (key == "ipv4_dst_mask"):
                addr = Matches.ipv4_to_int(config["ipv4_dst"])
                mask = Matches.mask_ntob(int(val))
                #mask = Matches.ipv4_to_int(val)
                matches.set_ipv4_dst_masked(addr, mask)

            elif (key == "tcp_src"):
                matches.set_tcp_src(int(val))

            elif (key == "tcp_dst"):
                matches.set_tcp_dst(int(val))

            elif (key == "udp_src"):
                matches.set_udp_src(int(val))

            elif (key == "udp_dst"):
                matches.set_udp_dst(int(val))

            elif (key == "sctp_src"):
                 matches.set_sctp_src(int(val))

            elif (key == "sctp_dst"):
                 matches.set_sctp_dst(int(val))

            elif (key == "icmpv4_type"):
                 matches.set_icmpv4_type(int(val))            

            elif (key == "icmpv4_code"):
                 matches.set_icmpv4_code(int(val))   

            elif (key == "arp_op"):
                raise Exception("Wrong match name:", key)

            elif (key == "arp_spa"):
                raise Exception("Wrong match name:", key)

            elif (key == "arp_tpa"):
                raise Exception("Wrong match name:", key)

            elif (key == "arp_sha"):
                raise Exception("Wrong match name:", key)

            elif (key == "arp_tha"):
                raise Exception("Wrong match name:", key)

            elif (key == "ipv6_src"):
                matches.set_ipv6_src(Matches.ipv6_to_int(val))
                
            elif (key == "ipv6_src_mask"):
                ipv6_src_int = Matches.ipv6_to_int(config["ipv6_src"])
                mask_int = Matches.ipv6_to_int(mask)
                match.set_ipv6_src_masked(ipv6_src_int, mask_int)             
                
            elif (key == "ipv6_dst"):
                matches.set_ipv6_dst(Matches.ipv6_to_int(val))

            elif (key == "ipv6_dst_mask"):
                ipv6_dst_int = Matches.ipv6_to_int(config["ipv6_dst"])
                mask_int = Matches.ipv6_to_int(mask)
                match.set_ipv6_dst_masked(ipv6_dst_int, mask_int) 
                
            elif (key == "ipv6_flabel"):
                lst = val.split(',')
                flabel_int = Utils.to_int(lst[0])                
                if(len(lst) == 1):
                    matches.set_ipv6_flabel(flabel_int)
                elif(len(lst) == 2):
                    flabel_mask_int = Utils.to_int(lst[1])
                    matches.set_ipv6_flabel_masked(flabel_int, flabel_mask_int)
                else:
                    print key, ": only two values allowed, key ignored"            
                 
            elif (key == "icmpv6_type"):
                 matches.set_icmpv6_type(int(val))   

            elif (key == "icmpv6_code"):
                 matches.set_icmpv6_code(int(val))   

            elif (key == "ipv6_nd_target"):
                raise Exception("Wrong match name:", key)

            elif (key == "ipv6_nd_sll"):
                raise Exception("Wrong match name:", key)

            elif (key == "ipv6_nd_tll"):
                raise Exception("Wrong match name:", key)

            elif (key == "mpls_label"):
                raise Exception("Wrong match name:", key)

            elif (key == "mpls_tc"):
                raise Exception("Wrong match name:", key)

            elif (key == "mpls_bos"):
                raise Exception("Wrong match name:", key)

            elif (key == "pbb_isid"):
                raise Exception("Wrong match name:", key)

            elif (key == "tunnel_id"):
                matches.set_tunnel_id(int(val))

            elif (key == "ipv6_exthdr"):
                raise Exception("Wrong match name:", key)

            else:
                raise Exception("Wrong match name:", key)

        #print "matches: %s" % matches
        return matches

    @staticmethod
    def ipv4_to_int(string):
        ip = string.split('.')
        assert len(ip) == 4
        i = 0
        for b in ip:
            b = int(b)
            i = (i << 8) | b
        return i
        
    @staticmethod
    def ipv6_to_int(string):
        ip = string.split(':')
        assert len(ip) == 8
        return [int(x, 16) for x in ip]

    @staticmethod
    def ipv4_text_to_int(ip_text):
        if ip_text == 0:
            return ip_text
        assert isinstance(ip_text, str)
        return struct.unpack('!I', addrconv.ipv4.text_to_bin(ip_text))[0]

    @staticmethod
    def mask_ntob(mask, err_msg=None):
        try:
            return (0xffffffff << (32 - mask)) & 0xffffffff
        except ValueError:
            msg = 'illegal netmask'
            if err_msg is not None:
                msg = '%s %s' % (err_msg, msg)
            raise ValueError(msg)



