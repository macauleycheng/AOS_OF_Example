01-Case: (offer the max number of matching fields -- ipv4)
   match: input physical port, DA, SA, EtherType, Tagged VID, Tagged priority, DIP, SIP, 
          IP protocol, TCP src port, TCP dest port, IP DSCP
   action: 
	change: DA, SA, VID
        output: a single port (tagged)

02-Case: (same as 01-Case, but using ECMP for output)
   match: input physical port, DA, SA, EtherType, Tagged VID, Tagged priority, DIP, SIP,
          IP protocol, TCP src port, TCP dest port, IP DSCP
   action:
        change: DA, SA, VID
        output: an ECMP interface

03-Case: (offer the max number of matching fields -- ipv6) (DA/SA matches can be supported on some products)
   match: input physical port, EtherType, Tagged VID, DIPv6, SIPv6,
          IP protocol, UDP src port, UDP dest port, IP DSCP, Flow Label
   action:
        change: DA, SA, VID
        output: a single port (tagged)

04-Case:
   match:  ICMPv4 type, ICMPv4 code
   action:
       output: a single port (untagged)

05-Case:
   match:  ICMPv6 type, ICMPv6 code
   action:
       output: a single port (untagged)

06-Case:
   match: SCTP src port, SCTP dest port
   action:
        output: a single port (untagged)

07-Case:
   match: tunnel ID
   action:
        output: a single port (untagged)




	 
