#!/usr/bin/env python3
import os
import time
import sys
sys.path.append('py-json')
import json
import pprint
from LANforge import LFRequest
from LANforge import LFUtils
import create_genlink as genl

if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit()

mgrURL = "http://localhost:8080/"


def execWrap(cmd):
	if os.system(cmd) != 0:
		print("\nError with " + cmd + ",bye\n")
		exit(1)

def jsonReq(mgrURL, reqURL, data, debug=False):
	lf_r = LFRequest.LFRequest(mgrURL + reqURL)
	lf_r.addPostData(data)

	if debug:
		json_response = lf_r.jsonPost(True)
		LFUtils.debug_printer.pprint(json_response)
		sys.exit(1)
	else:
		lf_r.jsonPost()
def getJsonInfo(mgrURL, reqURL, name):
	lf_r = LFRequest.LFRequest(mgrURL + reqURL)
	json_response = lf_r.getAsJson()
	print(name)
	print(json_response)
	#j_printer = pprint.PrettyPrinter(indent=2)
	#j_printer.pprint(record)


#create cx for tcp and udp
cmd = ("perl lf_firemod.pl --action create_cx --cx_name test1 --use_ports sta00000,eth1 --use_speeds  360000,150000 --endp_type tcp")
execWrap(cmd)
cmd = ("perl lf_firemod.pl --action create_cx --cx_name test2 --use_ports sta00000,eth1 --use_speeds  360000,150000 --endp_type udp")
execWrap(cmd)

#create l4 endpoint
url = "cli-json/add_l4_endp"
data = {
"alias":"l4Test",
"shelf":1,
"resource":1,
"port":"sta00000",
"type":"l4_generic",
"timeout":1000,
"url_rate":600,
"url":"dl http://10.40.0.1/ /dev/null"
}

jsonReq(mgrURL, url, data)

#create cx for l4_endp
url = "cli-json/add_cx"
data = {
"alias":"CX_l4Test",
"test_mgr":"default_tm",
"tx_endp":"l4Test",
"rx_endp":"NA"
}

jsonReq(mgrURL, url, data)

#create fileio endpoint
url = "cli-json/add_file_endp"
data = {
"alias":"fioTest",
"shelf":1,
"resource":1,
"port":"sta00000",
"type":"fe_nfs",
"directory":"/mnt/fe-test"
}

jsonReq(mgrURL,url,data)

#create fileio cx
url = "cli-json/add_cx"
data = {
"alias":"CX_fioTest",
"test_mgr":"default_tm",
"tx_endp":"fioTest",
"rx_endp":"NA"
}

jsonReq(mgrURL,url,data)


#create generic endpoint
genl.createGenEndp("genTest1",1,1,"sta00000","gen_generic")
genl.createGenEndp("genTest2",1,1,"sta00000","gen_generic")
genl.setFlags("genTest1","ClearPortOnStart",1)
genl.setFlags("genTest2","ClearPortOnStart",1)
genl.setFlags("genTest2","Unmanaged",1)
genl.setCmd("genTest1","lfping  -i 0.1 -I sta00000 10.40.0.1")

#create generic cx
url = "cli-json/add_cx" 
data = {
"alias":"CX_genTest1",
"test_mgr":"default_tm",
"tx_endp":"genTest1",
"rx_endp":"genTest2"
}

jsonReq(mgrURL,url,data)


#start cx traffic
cxNames = ["test1","test2", "CX_l4Test", "CX_fioTest", "CX_genTest1"]
for name in range(len(cxNames)):
	cmd = (f"perl lf_firemod.pl --mgr localhost --quiet 0 --action do_cmd --cmd \"set_cx_state default_tm {cxNames[name]} RUNNING\"")
	execWrap(cmd)

time.sleep(5)


#show tx and rx bytes for ports
time.sleep(5)
print("eth1")
cmd = ("perl ./lf_portmod.pl --quiet 1 --manager localhost --port_name eth1 --show_port \"Txb,Rxb\"")
execWrap(cmd)
print("sta00000")
cmd = ("perl ./lf_portmod.pl --quiet 1 --manager localhost --port_name sta00000 --show_port \"Txb,Rxb\"")
execWrap(cmd)


#show tx and rx for endpoints PERL
time.sleep(5)
print("test1-A")
cmd = ("./lf_firemod.pl --action show_endp --endp_name test1-A --endp_vals tx_bps,rx_bps")
execWrap(cmd)
print("test1-B")
cmd = ("./lf_firemod.pl --action show_endp --endp_name test1-B --endp_vals tx_bps,rx_bps")
execWrap(cmd)
print("test2-A")
cmd = ("./lf_firemod.pl --action show_endp --endp_name test2-A --endp_vals tx_bps,rx_bps")
execWrap(cmd)
print("test2-B")
cmd = ("./lf_firemod.pl --action show_endp --endp_name test2-B --endp_vals tx_bps,rx_bps")
execWrap(cmd)
print("l4Test")
cmd = ("./lf_firemod.pl --action show_endp --endp_name l4Test --endp_vals Bytes-Read-Total")
execWrap(cmd)
cmd = ("./lf_firemod.pl --action show_endp --endp_name fioTest")
execWrap(cmd)
cmd = ("./lf_firemod.pl --action show_endp --endp_name genTest1")
execWrap(cmd)

#show tx and rx for endpoints JSON
getJsonInfo(mgrURL, "endp/test1-A?fields=tx+bytes,rx+bytes", "test1-A")
getJsonInfo(mgrURL, "endp/test1-B?fields=tx+bytes,rx+bytes", "test1-B")
getJsonInfo(mgrURL, "endp/test2-A?fields=tx+bytes,rx+bytes", "test2-A")
getJsonInfo(mgrURL, "endp/test2-B?fields=tx+bytes,rx+bytes", "test2-B")
getJsonInfo(mgrURL, "layer4/l4Test?fields=bytes-rd", "l4Test")
getJsonInfo(mgrURL, "generic/genTest1?fields=last+results", "genTest1")

#stop cx traffic
for name in range(len(cxNames)):
	cmd = (f"perl lf_firemod.pl --mgr localhost --quiet 0 --action do_cmd --cmd \"set_cx_state default_tm {cxNames[name]} STOPPED\"")
	execWrap(cmd)


#get JSON info from webpage for ports and endps
url = ["port/","endp/"]
timeout = 5 # seconds

for i in range(len(url)):
	lf_r = LFRequest.LFRequest(mgrURL + url[i])
	json_response = lf_r.getAsJson()
	#print(json_response)
	j_printer = pprint.PrettyPrinter(indent=2)
	if not i:
		print("Ports: \n")
		for record in json_response['interfaces']:
			j_printer.pprint(record)
	else:
		print("Endpoints: \n")
		for record in json_response['endpoint']:
                        j_printer.pprint(record)
