#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python 3.6.3
# Copyright by Neil Judson
# Revision: 0.1 Date: 2018/01/08 20:00:00

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
        for i in dic_route_message_reg:
            route_message = re.search(dic_route_message_reg[i], s)
            if route_message:
                dic_route_detail.update({i: route_message.group()})
            else:
                dic_route_detail.update({i: ''})
        next_hop_0 = re.search(r'via ' + self.s_ip_reg, s)
        if next_hop_0:
            next_hop = re.search(self.ip_reg, next_hop_0.group())
            if next_hop:
                dic_route_detail.update({'NextHop': next_hop.group()})
            else:
                dic_route_detail.update({'NextHop': ''})
        return dic_route_detail
        # route_detail = ''
        # dic_route_message_reg = {
        #     'Type':         r'^[a-zA-Z]*',
        #     'AD/Metric':    r'\[\d*/\d*\]',
        #     'Interface':    r'((FastEthernet|Ethernet|Serial)\d*/\d*)|null0'
        # }
        # for i in dic_route_message_reg:
        #     route_message = re.search(dic_route_message_reg[i], s)
        #     if route_message:
        #         route_detail = route_detail + i + ':' + route_message.group() + ' | '
        #     else:
        #         route_detail = route_detail + i + ':' + ' | '
        # next_hop_0 = re.search(re.compile(r'via ' + self.s_ip_reg), s)
        # if next_hop_0:
        #     next_hop = re.search(self.ip_reg, next_hop_0.group())
        #     if next_hop:
        #         route_detail = route_detail + 'NextHop:' + next_hop.group()
        #     else:
        #         route_detail = route_detail + 'NextHop:'
        # # interface = re.search(r'((FastEthernet|Ethernet|Serial)\d*\/\d*)|null0', s)
        # # if interface:
        # #     route_detail = route_detail + 'Interface:' + interface.group() + ' | '
        # # else:
        # #     route_detail = route_detail + 'Interface:' + ' | '
        # return route_detail

    def compare_route_table(self, dic_table_1, dic_table_2):
        return dic_table_1 == dic_table_2


if __name__ == '__main__':
    rc = RouteCompare()
    dic_route_table_1 = rc.read_route_file('R1.log')
    for j in dic_route_table_1:
        print('%-18s' % j + ' ', dic_route_table_1[j])
    print([(k,  dic_route_table_1[k]) for k in sorted(dic_route_table_1.keys())])  # sort
    dic_route_table_2 = rc.read_route_file('R1.log')
    result = rc.compare_route_table(dic_route_table_1, dic_route_table_2)
    print(result)
