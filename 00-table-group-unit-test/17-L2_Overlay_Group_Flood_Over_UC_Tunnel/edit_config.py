import pkg_resources
pkg_resources.require("ncclient==0.4.3")
from ncclient import manager
import ncclient


#due to ofconfig design problem, it need fill port feature 
#but we won't use it currently.

#of-agent nexthop 2 destination user-input-dst-mac ethernet 1/2 vid 2
config_nexthop_ucast_xml="""
  <config>
      <of11-config:capable-switch xmlns:of11-config="urn:onf:of111:config:yang">
        <ofdpa10:next-hop xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
          <ofdpa10:id>2</ofdpa10:id>
          <ofdpa10:dest-mac>user-input-dst-mac</ofdpa10:dest-mac>
          <ofdpa10:phy-port>2</ofdpa10:phy-port>
          <ofdpa10:vid>2</ofdpa10:vid>
        </ofdpa10:next-hop>
      </of11-config:capable-switch>
  </config>
  """
  
#of-agent nexthop 20 destination 01-00-5e-01-01-01 ethernet 1/2 vid 2
config_nexthop_mcast_xml="""
  <config>
      <of11-config:capable-switch xmlns:of11-config="urn:onf:of111:config:yang">
        <ofdpa10:next-hop xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
          <ofdpa10:id>20</ofdpa10:id>
          <ofdpa10:dest-mac>01:00:5E:01:01:01</ofdpa10:dest-mac>
          <ofdpa10:phy-port>2</ofdpa10:phy-port>
          <ofdpa10:vid>2</ofdpa10:vid>
        </ofdpa10:next-hop>
      </of11-config:capable-switch>
  </config>
  """

#of-agent vni 10
config_vni_xml="""
  <config>
      <of11-config:capable-switch xmlns:of11-config="urn:onf:of111:config:yang">
        <ofdpa10:vni xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
          <ofdpa10:id>10</ofdpa10:id>
        </ofdpa10:vni>
      </of11-config:capable-switch>
  </config>
  """
  
  
#of-agent vtap 10001 ethernet 1/1 vid 1
#of-agent vtp 10001 vni 10
config_vtap_xml="""
  <config>
    <capable-switch xmlns="urn:onf:of111:config:yang">
      <id>capable-switch-1</id>
      <resources>
       <port>
         <resource-id>10001</resource-id>     
           <features>
             <current>
               <rate>10Gb</rate>
               <medium>fiber</medium>
               <pause>symmetric</pause>      
             </current>
             <advertised>
               <rate>10Gb</rate>
               <rate>100Gb</rate>
               <medium>fiber</medium>
               <pause>symmetric</pause>
             </advertised>    
             <supported>
               <rate>10Gb</rate>
               <rate>100Gb</rate>
               <medium>fiber</medium>
               <pause>symmetric</pause>
             </supported> 
             <advertised-peer>
               <rate>10Gb</rate>
               <rate>100Gb</rate>
               <medium>fiber</medium>
               <pause>symmetric</pause>
             </advertised-peer>        
           </features>
           <ofdpa10:vtap xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
             <ofdpa10:phy-port>1</ofdpa10:phy-port>
             <ofdpa10:vid>1</ofdpa10:vid>
             <ofdpa10:vni>10</ofdpa10:vni>
           </ofdpa10:vtap>
       </port> 
      </resources>
      <logical-switches>
          <switch>
            <id>user-input-switch-cpu-mac</id>
            <datapath-id>user-input-switch-cpu-mac</datapath-id>
            <resources>
              <port>10001</port>
            </resources>
          </switch>
      </logical-switches>
    </capable-switch>
  </config>
  """
  
#of-agent vtep 10002 source user-input-src-ip destination user-input-dst-ip udp-source-port 6633 nexthop 2 ttl 25
config_vtep_xml="""
  <config>
    <capable-switch xmlns="urn:onf:of111:config:yang">
      <id>capable-switch-1</id>
      <ofdpa10:udp-dest-port xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">6633</ofdpa10:udp-dest-port>
      <resources>
       <port>
         <resource-id>10002</resource-id>     
           <features>
             <current>
               <rate>10Gb</rate>
               <medium>fiber</medium>
               <pause>symmetric</pause>      
             </current>
             <advertised>
               <rate>10Gb</rate>
               <rate>100Gb</rate>
               <medium>fiber</medium>
               <pause>symmetric</pause>
             </advertised>    
             <supported>
               <rate>10Gb</rate>
               <rate>100Gb</rate>
               <medium>fiber</medium>
               <pause>symmetric</pause>
             </supported> 
             <advertised-peer>
               <rate>10Gb</rate>
               <rate>100Gb</rate>
               <medium>fiber</medium>
               <pause>symmetric</pause>
             </advertised-peer>        
           </features>
                <ofdpa10:vtep xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
                  <ofdpa10:src-ip>user-input-src-ip</ofdpa10:src-ip>
                  <ofdpa10:dest-ip>user-input-dst-ip</ofdpa10:dest-ip>
                  <ofdpa10:udp-src-port>6633</ofdpa10:udp-src-port>
                  <ofdpa10:vni>10</ofdpa10:vni>
                  <ofdpa10:nexthop-id>2</ofdpa10:nexthop-id>
                  <ofdpa10:ttl>25</ofdpa10:ttl>
                </ofdpa10:vtep>
       </port> 
      </resources>
      <logical-switches>
          <switch>
            <id>user-input-switch-cpu-mac</id>
            <datapath-id>user-input-switch-cpu-mac</datapath-id>
            <resources>
              <port>10002</port>
            </resources>
          </switch>
      </logical-switches>
    </capable-switch>
  </config>  
  """

def replace_vtep_vtap_nexthop(sip, dip, smac, dmac):
    global nexthop_ucast_xml
    nexthop_ucast_xml=config_nexthop_ucast_xml.replace("user-input-dst-mac", dmac)
	
    global vtep_xml
    vtep_xml=config_vtep_xml.replace("user-input-switch-cpu-mac", "00:00:"+smac)
    vtep_xml=vtep_xml.replace("user-input-src-ip", sip)
    vtep_xml=vtep_xml.replace("user-input-dst-ip", dip)
	
    global vtap_xml
    vtap_xml=config_vtap_xml.replace("user-input-switch-cpu-mac","00:00:"+smac)
    

def send_edit_config(host_ip, username, password):
    with manager.connect_ssh(host=host_ip, port=830, username=username, password=password, hostkey_verify=False ) as m:
        try:
            m.edit_config(target='running', 
                          config=nexthop_ucast_xml, 
                          default_operation='merge', 
                          error_option='stop-on-error')
        except Exception as e:
            print "Fail to edit-config config_nexthop_ucast_xml"
            return -1

        try:
            m.edit_config(target='running', 
                          config=config_nexthop_mcast_xml, 
                          default_operation='merge', 
                          error_option='stop-on-error')
        except Exception as e:
            print "Fail to edit-config config_nexthop_mcast_xml"
            return -1

        try:
            m.edit_config(target='running', 
                          config=config_vni_xml, 
                          default_operation='merge', 
                          error_option='stop-on-error')
        except Exception as e:
            print "Fail to edit-config config_vni_xml"	
            return -1
        		
        try:
            m.edit_config(target='running', 
                          config=vtep_xml, 
                          default_operation='merge', 
                          error_option='stop-on-error')
        except Exception as e:
            print "Fail to edit-config vtep_xml"	
            return -1

        try:
            m.edit_config(target='running', 
                          config=vtap_xml, 
                          default_operation='merge', 
                          error_option='stop-on-error')
        except Exception as e:
            print "Fail to edit-config vtap_xml"	
            return -1

    	print m.get_config(source='running').data_xml
    

#replace_vtep_vtap_nexthop("10.1.1.1", "10.1.2.1", "70:72:cf:dc:9e:da", "70:72:cf:b5:ea:88")
#send_edit_config("192.168.1.1", "netconfuser", "netconfuser")

