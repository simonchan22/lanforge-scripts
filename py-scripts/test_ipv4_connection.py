#!/usr/bin/env python3


import sys
import os
import argparse

if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit(1)

if 'py-json' not in sys.path:
    sys.path.append(os.path.join(os.path.abspath('..'), 'py-json'))
import LANforge
from LANforge.lfcli_base import LFCliBase
from LANforge import LFUtils
import realm
import time
import pprint


class IPv4Test(LFCliBase):
    def __init__(self, 
                 ssid,
                 security,
                 password,
                 host,
                 port,
                 sta_list=None,
                 number_template="00000",
                 radio="wiphy0",
                 _debug_on=False,
                 _exit_on_error=False,
                 _exit_on_fail=False):
        super().__init__(host,
                         port,
                         _debug=_debug_on,
                         _halt_on_error=_exit_on_error,
                         _exit_on_fail=_exit_on_fail)
        self.host = host
        self.port = port
        self.ssid = ssid
        self.security = security
        self.password = password
        self.sta_list = sta_list
        self.radio = radio
        self.timeout = 120
        self.number_template = number_template
        self.debug = _debug_on
        self.local_realm = realm.Realm(lfclient_host=self.host, lfclient_port=self.port)

        self.station_profile = self.local_realm.new_station_profile()
        self.station_profile.lfclient_url = self.lfclient_url
        self.station_profile.ssid = self.ssid
        self.station_profile.ssid_pass = self.password,
        self.station_profile.security = self.security
        self.station_profile.number_template_ = self.number_template
        self.station_profile.mode = 0
        if self.debug:
            print("----- Station List ----- ----- ----- ----- ----- ----- \n")
            pprint.pprint(self.sta_list)
            print("---- ~Station List ----- ----- ----- ----- ----- ----- \n")


    def build(self):
        # Build stations
        self.station_profile.use_security(self.security, self.ssid, self.password)
        self.station_profile.set_number_template(self.number_template)

        print("Creating stations")
        self.station_profile.set_command_flag("add_sta", "create_admin_down", 1)
        self.station_profile.set_command_param("set_port", "report_timer", 1500)
        self.station_profile.set_command_flag("set_port", "rpt_timer", 1)
        self.station_profile.create(radio=self.radio, sta_names_=self.sta_list, debug=self.debug)
        self._pass("PASS: Station build finished")

    def start(self, sta_list, print_pass, print_fail):
        self.station_profile.admin_up()
        associated_map = {}
        ip_map = {}
        print("Starting test...")
        for sec in range(self.timeout):
            for sta_name in sta_list:
                eidn = self.local_realm.name_to_eid(sta_name)
                url = "/port/1/%s/%s" % (eidn[1], eidn[2])
                sta_status = self.json_get(url + "?fields=port,alias,ip,ap", debug_=self.debug)
                # print(sta_status)
                if (sta_status is None) or (sta_status['interface'] is None) or (sta_status['interface']['ap'] is None):
                    continue
                if (len(sta_status['interface']['ap']) == 17) and (sta_status['interface']['ap'][-3] == ':'):
                    if self.debug:
                        print("Associated", sta_name, sta_status['interface']['ap'], sta_status['interface']['ip'])
                    associated_map[sta_name] = 1
                if sta_status['interface']['ip'] != '0.0.0.0':
                    if self.debug:
                        print("IP", sta_name, sta_status['interface']['ap'], sta_status['interface']['ip'])
                    ip_map[sta_name] = 1
            if (len(sta_list) == len(ip_map)) and (len(sta_list) == len(associated_map)):
                break
            else:
                time.sleep(1)

        if self.debug:
            print("sta_list", len(sta_list), sta_list)
            print("ip_map", len(ip_map), ip_map)
            print("associated_map", len(associated_map), associated_map)
        if (len(sta_list) == len(ip_map)) and (len(sta_list) == len(associated_map)):
            self._pass("PASS: All stations associated with IP", print_pass)
        else:
            self._fail("FAIL: Not all stations able to associate/get IP", print_fail)
            print("sta_list", sta_list)
            print("ip_map", ip_map)
            print("associated_map", associated_map)

        return self.passes()

    def stop(self):
        # Bring stations down
        self.station_profile.admin_down()

    def cleanup(self, sta_list):
        self.station_profile.cleanup(sta_list, debug_=self.debug)
        LFUtils.wait_until_ports_disappear(base_url=self.lfclient_url,
                                           port_list=sta_list,
                                           debug=self.debug)
        time.sleep(1)

def main():
    parser = LFCliBase.create_basic_argparse(
        prog='test_ipv4_connection.py',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''\
         Create stations that attempt to authenticate, associate, and receive IP addresses on the 
         chosen SSID
            ''',

        description='''\
        test_ipv4_connection.py
--------------------
Generic command example:
./test_ipv4_connection.py 
    --upstream_port eth1 
    --radio wiphy0 
    --num_stations 3 
    --security open 
    --ssid netgear 
    --passwd BLANK 
    --debug
            ''')
    required = parser.add_argument_group('required arguments')
    required.add_argument('--security', help='WiFi Security protocol: < open | wep | wpa | wpa2 | wpa3 >', required=True)

    args = parser.parse_args()
    if (args.radio is None):
       raise ValueError("--radio required")

    num_sta = 2
    if (args.num_stations is not None) and (int(args.num_stations) > 0):
        num_stations_converted = int(args.num_stations)
        num_sta = num_stations_converted

    station_list = LFUtils.port_name_series(prefix="sta",
                                          start_id=0,
                                          end_id=num_sta-1,
                                          padding_number=10000,
                                          radio=args.radio)

    ip_test = IPv4Test(host=args.mgr, port=args.mgr_port,
                       ssid=args.ssid,
                       password=args.passwd,
                       security=args.security,
                       sta_list=station_list,
                       radio=args.radio,
                       _debug_on=args.debug)
    ip_test.cleanup(station_list)
    ip_test.build()
    if not ip_test.passes():
        print(ip_test.get_fail_message())
        ip_test.add_event(name="test_ipv4_connection.py", message=ip_test.get_fail_message())
        ip_test.exit_fail()
    ip_test.start(station_list, False, False)
    ip_test.stop()
    if not ip_test.passes():
        print(ip_test.get_fail_message())
        ip_test.add_event(name="test_ipv4_connection.py", message=ip_test.get_fail_message())
        ip_test.exit_fail()
    time.sleep(30)
    ip_test.cleanup(station_list)
    if ip_test.passes():
        ip_test.add_event(name="test_ipv4_connection.py", message="Full test passed, all stations associated and got IP")
        ip_test.exit_success()
        

if __name__ == "__main__":
    main()
