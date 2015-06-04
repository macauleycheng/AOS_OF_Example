from ncclient import manager
import ncclient
import xml.etree.ElementTree as ET

host = "192.168.1.1"
username="root"
password="root"

           
config_xml="""
  <config>
    <capable-switch xmlns="urn:onf:of111:config:yang">
      <id>capable-switch-1</id>
      <udp-src-port-entropy xmlns="urn:bcm:ofdpa10:accton01">false</udp-src-port-entropy>
    </capable-switch>
  </config>
  """
  
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    #print m.server_capabilities
    print m.edit_config(target='running', 
                      config=config_xml, 
                      default_operation='merge', 
                      error_option='stop-on-error')

    print m.get_config(source='running').data_xml
