from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER , MAIN_DISPATCHER, DEAD_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu import utils
import edit_config	

class appExample(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	
    def __init__(self, *args, **kwargs):
        super(appExample , self).__init__(*args, **kwargs)

		
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        edit_config.replace_vtep_vtap_nexthop("10.1.1.1", "10.1.2.1", "70:72:cf:b5:ea:88", "70:72:cf:b5:ea:88")
        edit_config.send_edit_config("192.168.1.1", "root", "root")
		
		