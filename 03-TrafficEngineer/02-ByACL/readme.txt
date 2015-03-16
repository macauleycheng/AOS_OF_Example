01-Case: (offer the max number of matching fields)
   match: input physical port, DA, SA, EtherType, Tagged VID, Tagged priority, DIP, SIP, 
          IP protocol, TCP src port, TCP dest port, IP DSCP
   action: 
	change: DA, SA, VID
        output: a single port (tagged)

02-Case:
   match: tunnel ID, EtherType, IPv6 Flow Label, UDP src port, UDP dest port
   action:
        change: DA, SA, VID
        output: a single port (tagged)


03-Case:
   match: SCTP src port, SCTP dest port
   action:
        output: a single port (tagged)

04-Case:
   match:  ICMPv4 type, ICMPv4 code
   action:
       output: an ECMP interface

05-Case:
   match:  ICMPv6 type, ICMPv6 code
   action:
       output: a single port (tagged)




	 
