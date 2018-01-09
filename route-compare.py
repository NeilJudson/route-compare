#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python 3.6.3
# Copyright by Neil Judson
# Revision: 0.2 Date: 2018/01/09 15:30:00

# import sys
import re
import chardet


class RouteCompare:
    s_ip_reg = r'(((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(/[1-3]?\d)?)'
    ip_reg = re.compile(s_ip_reg)

    def read_route_file(self, s_file_name):
        f = None
        encode_type = None

        try:
            f = open(s_file_name, 'rb')
        except FileNotFoundError:
            print('Can not find file: ' + s_file_name)
            exit(-1)
        try:
            s = f.read()
            encode_type = chardet.detect(s)['encoding']
        except Exception as e1:
            print('ERROR1: ', e1)
            exit(-1)
        finally:
            f.close()

        try:
            f = open(s_file_name, encoding=encode_type)
        except FileNotFoundError:
            print('Can not find file: ' + s_file_name)
            exit(-1)
        try:
            s = f.readline()
            s_net_ip = '0.0.0.0/32'
            s_net_mask = '/32'
            dic_route_table = {}
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
        except Exception as e2:
            print('ERROR1: ', e2)
            exit(-1)
        finally:
            f.close()

    def get_route_detail(self, s):
        dic_route_detail = {}
        dic_route_message_reg = {
            'Type': r'^[a-zA-Z]*',
            'AD/Metric': r'\[\d*/\d*\]',
            'Interface': r'((FastEthernet|Ethernet|Serial)\d*/\d*)|null0'
        }

        for j in dic_route_message_reg:
            route_message = re.search(dic_route_message_reg[j], s)
            if route_message:
                dic_route_detail.update({j: route_message.group()})
            else:
                dic_route_detail.update({j: ''})
        next_hop0 = re.search(r'via ' + self.s_ip_reg, s)
        if next_hop0:
            next_hop = re.search(self.ip_reg, next_hop0.group())
            if next_hop:
                dic_route_detail.update({'NextHop': next_hop.group()})
            else:
                dic_route_detail.update({'NextHop': ''})
        return dic_route_detail

    def compare_route_table(self, dic_table_1, dic_table_2):
        table_1_keys = dic_table_1.keys()
        table_2_keys = dic_table_2.keys()
        set_table_1_2_keys = table_1_keys - (table_1_keys - table_2_keys)  # both in table_1 and table_2
        for j in set_table_1_2_keys:
            # delete the same item
            if dic_table_1[j] == dic_table_2[j]:
                dic_table_1.pop(j)
                dic_table_2.pop(j)
        for j in dic_table_1:
            print('%-18s' % j + ' ', dic_table_1[j])
        print()
        for j in dic_table_2:
            print('%-18s' % j + ' ', dic_table_2[j])


if __name__ == '__main__':
    rc = RouteCompare()
    dic_route_table_1 = rc.read_route_file('R1.log')
    # for i in dic_route_table_1:
    #     print('%-18s' % i + ' ', dic_route_table_1[i])
    # print([(k,  dic_route_table_1[k]) for k in sorted(dic_route_table_1.keys())])  # sort
    dic_route_table_2 = rc.read_route_file('R1.log')
    if dic_route_table_1 == dic_route_table_2:
        print('These two route tables are the same.')
    else:
        print('These two route tables are different.')
        rc.compare_route_table(dic_route_table_1, dic_route_table_2)
