from ncclient import manager
import ncclient
import xml.etree.ElementTree as ET

host = "192.168.1.1"
username="root"
password="root"

config_next_hop_xml="""
  <config>
      <of11-config:capable-switch xmlns:of11-config="urn:onf:of111:config:yang">
        <ofdpa10:next-hop xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
          <ofdpa10:id>10</ofdpa10:id>
        </ofdpa10:next-hop>
      </of11-config:capable-switch>
  </config>
  """
  
config_xml="""
  <config>
      <of11-config:capable-switch xmlns:of11-config="urn:onf:of111:config:yang">
        <ofdpa10:next-hop xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
          <ofdpa10:id>20</ofdpa10:id>
          <ofdpa10:vid>1</ofdpa10:vid>
        </ofdpa10:next-hop>
      </of11-config:capable-switch>
  </config>
  """
  
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    print "Delete NextHop"
    print m.edit_config(target='running', 
                      config=config_next_hop_xml, 
                      default_operation='delete', 
                      error_option='stop-on-error')

    print "Delete ECMP group"
    print m.edit_config(target='running', 
                      config=config_xml, 
                      default_operation='delete', 
                      error_option='stop-on-error')

    print m.get_config(source='running').data_xml
