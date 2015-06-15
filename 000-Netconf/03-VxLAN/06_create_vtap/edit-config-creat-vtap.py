from ncclient import manager
import ncclient
import xml.etree.ElementTree as ET

host = "192.168.1.1"
username="netconfuser"
password="netconfuser"

#due to ofconfig design problem, it need fill port feature 
#but we won't use it currently.

config_vni_xml="""
  <config>
      <of11-config:capable-switch xmlns:of11-config="urn:onf:of111:config:yang">
        <ofdpa10:vni xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
          <ofdpa10:id>10</ofdpa10:id>
        </ofdpa10:vni>
      </of11-config:capable-switch>
  </config>
  """

config_xml="""
  <config>
    <capable-switch xmlns="urn:onf:of111:config:yang">
      <id>capable-switch-1</id>
      <resources>
       <port>
         <resource-id>10005</resource-id>     
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
             <ofdpa10:vid>4093</ofdpa10:vid>
             <ofdpa10:vni>10</ofdpa10:vni>
           </ofdpa10:vtap>
       </port> 
      </resources>
      <logical-switches>
          <switch>
            <id>00:00:70:72:cf:dc:9e:da</id>
            <datapath-id>00:00:70:72:cf:dc:9e:da</datapath-id>
            <resources>
              <port>10005</port>
            </resources>
          </switch>
      </logical-switches>
    </capable-switch>
  </config>
  """
  
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    print m.edit_config(target='running', 
                      config=config_vni_xml, 
                      default_operation='merge', 
                      error_option='stop-on-error')
                      
    print m.edit_config(target='running', 
                      config=config_xml, 
                      default_operation='merge', 
                      error_option='stop-on-error')

    print m.get_config(source='running').data_xml
