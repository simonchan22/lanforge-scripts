#!/usr/bin/env python3

# Example of how to instantiate StaConnect and run the test

import sys

if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit(1)
if 'py-json' not in sys.path:
    sys.path.append('../py-json')

# if you lack __init__.py in this directory you will not find sta_connect module
from sta_connect import StaConnect


def main():
    staConnect = StaConnect("localhost", 8080)
    staConnect.sta_mode = 0
    staConnect.upstream_resource = 1
    staConnect.upstream_port = "eth1"
    staConnect.radio = "wiphy0"
    staConnect.resource = 1
    staConnect.dut_ssid = "jedway-wpa2-x2048-5-1"
    staConnect.dut_passwd = "jedway-wpa2-x2048-5-1"
    staConnect.run()
    is_passing = staConnect.passes()
    if is_passing == False:
        # run_results = staConnect.get_failed_result_list()
        fail_message = staConnect.get_fail_message()
        print("Some tests failed:\n" + fail_message)
    else:
        print("Tests pass")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


if __name__ == '__main__':
    main()

#