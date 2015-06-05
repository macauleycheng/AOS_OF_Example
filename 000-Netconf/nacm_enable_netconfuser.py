from ncclient import manager
import ncclient
import xml.etree.ElementTree as ET

host = "192.168.1.1"
username="netconfuser"
password="netconfuser"

            
config_xml="""
<config>
    <nacm xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-acm">
        <rule-list>
            <name>netconfuser</name>
            <group>root</group>
            <rule>
                <name>permit-all</name>
                <module-name>*</module-name>
                <access-operations>*</access-operations>
                <action>permit</action>
            </rule>
        </rule-list>
    </nacm>
</config>
  """
  
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    #print m.server_capabilities
    print m.edit_config(target='startup', 
                      config=config_xml, 
                      default_operation='merge', 
                      error_option='stop-on-error')

    print m.get_config(source='running').data_xml
