#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

sys.path.append('../')

from route_compare import *


def main():
    try:
        route_table_old = get_route_table(sys.argv[3], sys.argv[1])
        route_table_new = get_route_table(sys.argv[3], sys.argv[2])
    except Exception as e:
        print(e)
        return
    result = compare_route_table(route_table_old, route_table_new)
    show_result_table(result, sys.argv[1], sys.argv[2])
    print(result_to_web(result))
    sys.exit()


if __name__ == '__main__':
    main()
