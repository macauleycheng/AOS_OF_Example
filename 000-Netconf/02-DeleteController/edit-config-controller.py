from ncclient import manager
import ncclient
import xml.etree.ElementTree as ET

host = "192.168.1.1"
username="root"
password="root"

##NOTE:
# below two colum shall change to switch CPU MAC
#            <id>00:00:70:72:cf:dc:9d:b2</id>
#            <datapath-id>00:00:70:72:cf:dc:9d:b2</datapath-id>

add_controller_xml="""
  <config>
    <capable-switch xmlns="urn:onf:of111:config:yang">
      <id>capable-switch-1</id>
        <logical-switches>
          <switch>
            <id>00:00:70:72:cf:dc:9d:b2</id>
            <datapath-id>00:00:70:72:cf:dc:9d:b2</datapath-id>
            <controllers>
              <controller>
                <id>192.168.10.105:6633</id>
                <ip-address>192.168.10.105</ip-address>
                <port>6633</port>
              </controller>
            </controllers>
          </switch>
        </logical-switches>
      </capable-switch>
  </config>
  """
  
del_controller_xml="""
  <config>
    <capable-switch
	xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
	xmlns="urn:onf:of111:config:yang">
      <id>capable-switch-1</id>
        <logical-switches>
          <switch>
            <id>00:00:70:72:cf:dc:9d:b2</id>
            <datapath-id>00:00:70:72:cf:dc:9d:b2</datapath-id>
            <controllers>
              <controller xc:operation="delete">
                <id>192.168.10.105:6633</id>
              </controller>
            </controllers>
          </switch>
        </logical-switches>
      </capable-switch>
  </config> 
  """
  
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    #print m.server_capabilities
    print m.edit_config(target='running', 
                      config=add_controller_xml, 
                      default_operation='merge', 
                      error_option='stop-on-error')

    print m.get_config(source='running').data_xml   
                     
    print m.edit_config(target='running', 
                        config=del_controller_xml, 
                        default_operation='none', 
                        error_option='stop-on-error')

    print m.get_config(source='running').data_xml
    print xml_str
