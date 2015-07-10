from ncclient import manager
import ncclient
import xml.etree.ElementTree as ET

host = "192.168.1.1"
username="netconfuser"
password="netconfuser"

           
config_xml="""
  <config>
    <capable-switch
    xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
    xmlns="urn:onf:of111:config:yang">
        <ofdpa10:next-hop
        xc:operation="delete"
        xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
          <ofdpa10:id>20</ofdpa10:id>
        </ofdpa10:next-hop>
    </capable-switch>
  </config>
  """
  
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    #print m.server_capabilities
    print m.edit_config(target='running', 
                      config=config_xml, 
                      default_operation='delete', 
                      error_option='stop-on-error')

    print m.get_config(source='running').data_xml
