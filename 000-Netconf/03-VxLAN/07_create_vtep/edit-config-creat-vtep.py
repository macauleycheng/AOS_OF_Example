from ncclient import manager
import ncclient
import xml.etree.ElementTree as ET

host = "192.168.1.1"
username="root"
password="root"

#due to ofconfig design problem, it need fill port feature
#but we won't use it currently. 
 
config_xml="""
  <config>
    <capable-switch xmlns="urn:onf:of111:config:yang">
      <id>capable-switch-1</id>
      <ofdpa10:udp-dest-port xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">6633</ofdpa10:udp-dest-port>
      <resources>
       <port>
         <resource-id>100000</resource-id>     
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
                  <ofdpa10:src-ip>10.1.2.3</ofdpa10:src-ip>
                  <ofdpa10:dest-ip>10.1.1.1</ofdpa10:dest-ip>
                  <ofdpa10:udp-src-port>6633</ofdpa10:udp-src-port>
                  <ofdpa10:vni>10</ofdpa10:vni>
                  <ofdpa10:nexthop-id>10</ofdpa10:nexthop-id>
                  <ofdpa10:ecmp-id>10</ofdpa10:ecmp-id>
                  <ofdpa10:ttl>25</ofdpa10:ttl>
                </ofdpa10:vtep>
       </port> 
      </resources>
      <logical-switches>
          <switch>
            <id>00:00:70:72:cf:b5:ea:88</id>
            <datapath-id>00:00:70:72:cf:b5:ea:88</datapath-id>
            <resources>
              <port>100000</port>
            </resources>
          </switch>
      </logical-switches>
    </capable-switch>

  </config>  """
  
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    print m.edit_config(target='running', 
                      config=config_xml, 
                      default_operation='merge', 
                      error_option='stop-on-error')

    print m.get_config(source='running').data_xml
