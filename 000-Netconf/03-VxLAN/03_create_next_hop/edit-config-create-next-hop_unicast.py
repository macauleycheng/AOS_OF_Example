from ncclient import manager
import ncclient
import xml.etree.ElementTree as ET

host = "192.168.1.1"
username="netconfuser"
password="netconfuser"

           
config_xml="""
  <config>
      <of11-config:capable-switch xmlns:of11-config="urn:onf:of111:config:yang">
        <ofdpa10:next-hop xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
          <ofdpa10:id>20</ofdpa10:id>
          <ofdpa10:dest-mac>00:00:11:22:33:44</ofdpa10:dest-mac>
          <ofdpa10:phy-port>1</ofdpa10:phy-port>
          <ofdpa10:vid>1</ofdpa10:vid>
        </ofdpa10:next-hop>
      </of11-config:capable-switch>
  </config>
  """
  
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    #print m.server_capabilities
    print m.edit_config(target='running', 
                      config=config_xml, 
                      default_operation='merge', 
                      error_option='stop-on-error')

    print m.get_config(source='running').data_xml
