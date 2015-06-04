from ncclient import manager
import ncclient
import xml.etree.ElementTree as ET

host = "192.168.1.1"
username="root"
password="root"

  
config_xml="""
  <config>
      <of11-config:capable-switch xmlns:of11-config="urn:onf:of111:config:yang">
        <ofdpa10:ecmp xmlns:ofdpa10="urn:bcm:ofdpa10:accton01">
          <ofdpa10:id>10</ofdpa10:id>
          <ofdpa10:nexthop-id>10</ofdpa10:nexthop-id>
        </ofdpa10:ecmp>
      </of11-config:capable-switch>
  </config>
  """

  
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    print "Delete ECMP Group"
    print m.edit_config(target='running', 
                      config=config_xml, 
                      default_operation='delete', 
                      error_option='stop-on-error')

    print m.get_config(source='running').data_xml
