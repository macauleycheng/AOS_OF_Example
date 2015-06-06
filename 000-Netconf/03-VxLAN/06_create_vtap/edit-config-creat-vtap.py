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
      <resources>
       <port>
         <resource-id>65538</resource-id>     
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
             <ofdpa10:phy-port>6633</ofdpa10:phy-port>
             <ofdpa10:vid>4093</ofdpa10:vid>
             <ofdpa10:vni>10</ofdpa10:vni>
           </ofdpa10:vtap>
       </port> 
      </resources>
      <logical-switches>
          <switch>
            <id>00:00:70:72:cf:b5:ea:88</id>
            <datapath-id>00:00:70:72:cf:b5:ea:88</datapath-id>
            <resources>
              <port>65538</port>
            </resources>
          </switch>
      </logical-switches>
    </capable-switch>

  </config>
  """
  
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    print m.edit_config(target='running', 
                      config=config_xml, 
                      default_operation='merge', 
                      error_option='stop-on-error')

    print m.get_config(source='running').data_xml
