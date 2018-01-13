#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python 3.6.3
# Copyright by Neil Judson
# Revision: 0.6 Date: 2018/01/11 22:00:00

import sys
import re
import chardet


class RouteCompare:
    s_ip_reg = r'(((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(/[1-3]?\d)?)'
    ip_reg = re.compile(s_ip_reg)

    def read_route_file(self, file_name):
        with open(file_name, 'rb') as f:
            s = f.read()
            encode_type = chardet.detect(s)['encoding']

        dic_route_table = {}

        with open(file_name, encoding=encode_type) as f:
            s_net_ip = '0.0.0.0/32'
            s_net_mask = '/32'

            s = f.readline()
            while s:
                ip = re.search(self.ip_reg, s)
                if ip:
                    if re.search('is[a-z ]*subnetted', s):
                        # subnetted net
                        net_mask = re.search(r'/[1-3]?\d', ip.group())
                        if net_mask:
                            s_net_mask = net_mask.group()
                    elif re.search('^ *\[\d*/\d*\]', s):
                        # multipath route
                        dic_route_detail = self.get_route_detail(s)  # analyse route entry
                        type_temp = dic_route_table[s_net_ip][0]['Type']
                        dic_route_detail.update({'Type': type_temp})
                        if {'Type': type_temp} == dic_route_table[s_net_ip][0]:
                            dic_route_table.update({s_net_ip: [dic_route_detail]})
                        else:
                            dic_route_table.update({s_net_ip: dic_route_table[s_net_ip] + [dic_route_detail]})
                        # How to sort of list of dict?
                    else:
                        # route
                        if re.search(r'/[1-3]?\d', ip.group()):
                            s_net_ip = ip.group()
                        else:
                            s_net_ip = ip.group() + s_net_mask
                        dic_route_detail = self.get_route_detail(s)  # analyse route entry
                        dic_route_table.update({s_net_ip: [dic_route_detail]})
                s = f.readline()
        return dic_route_table

    def get_route_detail(self, s):
        dic_route_detail = {}
        dic_route_message_reg = {
            'Type': r'^[CSRMBDOi*]([* ]{1,2}(EX|IA|N1|N2|E1|E2|su|L1|L2|ia]))?',
            'AD/Metric': r'\[\d*/\d*\]',
            'Interface': r'((FastEthernet|Ethernet|Serial)\d*/[\d.]*)|Loopback\d*|Port-channel\d*|Vlan\d*|Null0'
        }

        for j in dic_route_message_reg:
            route_message = re.search(dic_route_message_reg[j], s)
            if route_message:
                dic_route_detail.update({j: route_message.group()})
        next_hop0 = re.search(r'via ' + self.s_ip_reg, s)
        if next_hop0:
            next_hop = re.search(self.ip_reg, next_hop0.group())
            if next_hop:
                dic_route_detail.update({'NextHop': next_hop.group()})
        return dic_route_detail

    @staticmethod
    def compare_route_table(list_dic_table):
        list_table_keys = [list_dic_table[0].keys(), list_dic_table[1].keys()]
        set_table_keys_1_mul_2 = list_table_keys[0] - (list_table_keys[0] - list_table_keys[1])  # keys of table_1 and table_2
        set_table_keys_1_and_2 = list_table_keys[0] | list_table_keys[1]  # keys of table_1 or table_2
        for j in set_table_keys_1_mul_2:
            # delete the same item
            if list_dic_table[0][j] == list_dic_table[1][j]:
                set_table_keys_1_and_2.remove(j)
        return set_table_keys_1_and_2

    @staticmethod
    def show_result(set_result_keys, list_file_name, list_dic_table):
        print('These are %d different routes.' % len(set_result_keys))
        for m in sorted(set_result_keys):
            print(64 * '-')
            print('%-18s' % m)
            for n in [0, 1]:
                s = list_file_name[n] + ' '
                if m in list_dic_table[n]:
                    count = 0
                    length = len(list_dic_table[n][m])
                    j = len(list_file_name[n])
                    for l in list_dic_table[n][m]:
                        count += 1
                        # for p, q in l.items():
                        #     s += ' {p}:{q}'.format(p=p, q=q)
                        for q in l.values():
                            s += ' ' + q
                        if count != length:
                            s += '\n ' + j*' '
                print(s)
        print('\nThese are %d different routes.' % len(set_result_keys))


if __name__ == '__main__':
    list_argv = ['', '']
    list_dic_route_table = [{}, {}]
    sys_argv_len = len(sys.argv)
    if sys_argv_len == 3:
        list_argv = [sys.argv[1], sys.argv[2]]
    elif sys_argv_len == 2:
        print('Please input the name of table B: ')
        list_argv = [sys.argv[1], input()]
    else:
        print('Please input the name of table A: ')
        list_argv[0] = input()
        print('Please input the name of table B: ')
        list_argv[1] = input()

    rc = RouteCompare()
    list_dic_route_table[0] = rc.read_route_file(list_argv[0])
    list_dic_route_table[1] = rc.read_route_file(list_argv[1])
    # for i in dic_route_table_1:
    #     print('%-18s' % i + ' ', dic_route_table_1[i])
    # print([(k,  dic_route_table_1[k]) for k in sorted(dic_route_table_1.keys())])  # sort
    if list_dic_route_table[0] == list_dic_route_table[1]:
        print('These two route tables are the same.')
    else:
        print('These two route tables are different.')
        RouteCompare.show_result(RouteCompare.compare_route_table(list_dic_route_table), list_argv, list_dic_route_table)
