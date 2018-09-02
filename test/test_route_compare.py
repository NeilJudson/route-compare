#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Python 3.6

import sys

sys.path.append('../')

from route_compare import *


def main():
    if len(sys.argv) == 4:
        file_name_old = sys.argv[1]
        file_name_new = sys.argv[2]
        route_os = sys.argv[3]
    else:
        file_name_old = 'show_ip_route_C7KA.txt'
        file_name_new = 'show_ip_route_C7KB.txt'
        route_os = 'NXOS'
    try:
        route_table_old = get_route_table(route_os, file_name_old)
        route_table_new = get_route_table(route_os, file_name_new)
    except Exception as e:
        print(e)
        sys.exit()
    result = compare_route_table(route_table_old, route_table_new)
    show_result_table(result, file_name_old, file_name_new)
    print(result_to_web(result))
    sys.exit()


if __name__ == '__main__':
    main()
