from ncclient import manager
import ncclient
import xml.etree.ElementTree as ET

host = "192.168.1.1"
username="netconfuser"
password="netconfuser"

config_vni_xml="""
  <config>
      <of11-config:capable-switch xmlns:of11-config="urn:onf:of111:config:yang">
        <ofdpa10:vni xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
          <ofdpa10:id>101</ofdpa10:id>
        </ofdpa10:vni>
      </of11-config:capable-switch>
  </config>
  """
config_nexthop_xml="""
  <config>
      <of11-config:capable-switch xmlns:of11-config="urn:onf:of111:config:yang">
        <ofdpa10:next-hop xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
          <ofdpa10:id>1</ofdpa10:id>
          <ofdpa10:dest-mac>00:00:00:11:22:33</ofdpa10:dest-mac>
          <ofdpa10:phy-port>1</ofdpa10:phy-port>
          <ofdpa10:vid>2</ofdpa10:vid>
        </ofdpa10:next-hop>
      </of11-config:capable-switch>
  </config>
  """

#due to ofconfig design problem, it need fill port feature
#but we won't use it currently. 
#It need change below two value according to your SWITCH CPU MAC
#<id>00:00:70:72:cf:dc:9d:b2</id>
#<datapath-id>00:00:70:72:cf:dc:9d:b2</datapath-id> 
  
config_xml="""
  <config>
    <capable-switch xmlns="urn:onf:of111:config:yang">
      <id>capable-switch-1</id>
      <resources>
       <port>
         <resource-id>10006</resource-id>     
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
                  <ofdpa10:src-ip>192.168.2.1</ofdpa10:src-ip>
                  <ofdpa10:dest-ip>192.168.2.2</ofdpa10:dest-ip>
                  <ofdpa10:udp-src-port>65535</ofdpa10:udp-src-port>
                  <ofdpa10:vni>101</ofdpa10:vni>
                  <ofdpa10:nexthop-id>1</ofdpa10:nexthop-id>
                  <ofdpa10:ttl>255</ofdpa10:ttl>
                </ofdpa10:vtep>
       </port> 
      </resources>
      <logical-switches>
          <switch>
            <id>00:00:70:72:cf:dc:9e:da</id>
            <datapath-id>00:00:70:72:cf:dc:9e:da</datapath-id>
            <resources>
              <port>10006</port>
            </resources>
          </switch>
      </logical-switches>      
    </capable-switch>
  </config>
  """
  
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    print m.get_config(source='running').data_xml
    
    print "Create VNI"
    try:
        print m.edit_config(target='running', 
                           config=config_vni_xml, 
                           default_operation='merge', 
                           error_option='stop-on-error')
    except Exception as rpc_error:
        print rpc_error
        exit();

    print "Create NextHop"
    try:
        print m.edit_config(target='running', 
                           config=config_nexthop_xml, 
                           default_operation='merge', 
                           error_option='stop-on-error')
    except Exception as rpc_error:
        print rpc_error
        exit();
        
    print "Create VTEP"
    try:
        print m.edit_config(target='running', 
                           config=config_xml, 
                           default_operation='merge', 
                           error_option='stop-on-error')
    except Exception as rpc_error:
        print rpc_error
        exit();

    print m.get_config(source='running').data_xml
