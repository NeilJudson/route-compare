#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python 3.6.3
# Copyright by Neil Judson
# Revision: 0.3 Date: 2018/01/09 20:00:00

# import sys
import re
import chardet


class RouteCompare:
    s_ip_reg = r'(((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(/[1-3]?\d)?)'
    ip_reg = re.compile(s_ip_reg)

    def read_route_file(self, s_file_name):
        with open(s_file_name, 'rb') as f:
            s = f.read()
            encode_type = chardet.detect(s)['encoding']

        dic_route_table = {}

        with open(s_file_name, encoding=encode_type) as f:
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
                        dic_route_detail.update({'Type': dic_route_table[s_net_ip]['Type']})
                        dic_route_table.update({s_net_ip: [dic_route_table[s_net_ip], dic_route_detail]})
                    else:
                        # route
                        sub_net_mask = re.search(r'/[1-3]?\d', ip.group())
                        if sub_net_mask:
                            s_net_ip = ip.group()
                        else:
                            s_net_ip = ip.group() + s_net_mask
                        dic_route_detail = self.get_route_detail(s)  # analyse route entry
                        dic_route_table.update({s_net_ip: dic_route_detail})
                s = f.readline()
        return dic_route_table

    def get_route_detail(self, s):
        dic_route_detail = {}
        dic_route_message_reg = {
            'Type': r'^[a-zA-Z]*',
            'AD/Metric': r'\[\d*/\d*\]',
            'Interface': r'((FastEthernet|Ethernet|Serial)\d*/[\d.]*)|Vlan\d*|Null0'
        }

        for j in dic_route_message_reg:
            route_message = re.search(dic_route_message_reg[j], s)
            if route_message:
                dic_route_detail.update({j: route_message.group()})
            # else:
            #     dic_route_detail.update({j: ''})
        next_hop0 = re.search(r'via ' + self.s_ip_reg, s)
        if next_hop0:
            next_hop = re.search(self.ip_reg, next_hop0.group())
            if next_hop:
                dic_route_detail.update({'NextHop': next_hop.group()})
            # else:
            #     dic_route_detail.update({'NextHop': ''})
        return dic_route_detail

    def compare_route_table(self, dic_table_1, dic_table_2):
        table_keys_1 = dic_table_1.keys()
        table_keys_2 = dic_table_2.keys()
        set_table_keys_1_mul_2 = table_keys_1 - (table_keys_1 - table_keys_2)  # keys of table_1 and table_2
        set_table_keys_1_and_2 = table_keys_1 | table_keys_2           # keys of table_1 or table_2
        for j in set_table_keys_1_mul_2:
            # delete the same item
            if dic_table_1[j] == dic_table_2[j]:
                # dic_table_1.pop(j)
                # dic_table_2.pop(j)
                set_table_keys_1_and_2.remove(j)
        return set_table_keys_1_and_2


if __name__ == '__main__':
    rc = RouteCompare()
    dic_route_table_1 = rc.read_route_file('R1.log')
    # for i in dic_route_table_1:
    #     print('%-18s' % i + ' ', dic_route_table_1[i])
    # print([(k,  dic_route_table_1[k]) for k in sorted(dic_route_table_1.keys())])  # sort
    dic_route_table_2 = rc.read_route_file('R2.log')
    if dic_route_table_1 == dic_route_table_2:
        print('These two route tables are the same.')
    else:
        print('These two route tables are different.')
        set_result_keys = rc.compare_route_table(dic_route_table_1, dic_route_table_2)
        print('These are %d different routes.' % len(set_result_keys))
        for i in sorted(set_result_keys):
            print(150*'-')
            print('%-18s ' % i, (i in dic_route_table_1 and dic_route_table_1[i] or ''))
            print(19*' ', (i in dic_route_table_2 and dic_route_table_2[i] or ''))
