from ncclient import manager
import ncclient
import xml.etree.ElementTree as ET

host = "192.168.1.1"
username="root"
password="root"

           
with manager.connect_ssh(host=host, port=830, username=username, password=password, hostkey_verify=False ) as m:
    print m.get_config(source='startup').data_xml
