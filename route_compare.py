#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python 3.6.3
# Copyright by Neil Judson
# Revision: 0.8.4 Date: 2018/01/29 21:20:00

import sys
import os
import re
import chardet
import prettytable


class RouteCompare(object):
    IP_REG = re.compile(r'((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(/[1-3]?\d)?')
    DIC_ROUTE_MESSAGE_REG = {
        'Type': re.compile(r'^[LCSRMBDOi]([* ]{1,2}(EX|IA|N1|N2|E1|E2|su|L1|L2|ia]))?'),
        'Interface': re.compile(r'((TenGigabitEthernet|GigabitEthernet|FastEthernet|Ethernet|Serial)\d*[/\d.]*)|(Loopback|Port-channel|Vlan)\d*|Null0')
    }
    NEXT_HOP_REG = re.compile(r'via ((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(/[1-3]?\d)?')

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
                ip = re.search(self.IP_REG, s)
                if ip:
                    if re.search('is[a-z ]*subnetted', s):
                        # subnetted net
                        net_mask = re.search(r'/[1-3]?\d', ip.group())
                        if net_mask:
                            s_net_mask = net_mask.group()
                    elif re.search(r'^ *\[\d*/\d*\]', s):
                        # multipath route
                        dic_route_detail = self.get_route_detail(s)
                        try:
                            type_temp = dic_route_table[s_net_ip][0]['Type']
                            dic_route_detail.update({'Type': type_temp})
                            if {'Type': type_temp} == dic_route_table[s_net_ip][0]:
                                # 针对如下换行的情况：
                                # O       2.2.2.2
                                #                 [110/2] via 12.1.1.2, 00:47:24, FastEthernet1/1
                                dic_route_table[s_net_ip] = [dic_route_detail]
                            else:
                                dic_route_table[s_net_ip].append(dic_route_detail)
                        except Exception as e1:
                            pass # 路由表文件此处有问题
                    else:
                        # route
                        if re.search(r'/[1-3]?\d', ip.group()):
                            s_net_ip = ip.group()
                        else:
                            s_net_ip = ip.group() + s_net_mask
                        dic_route_detail = self.get_route_detail(s)
                        dic_route_table.update({s_net_ip: [dic_route_detail]})
                s = f.readline()
        return dic_route_table

    def get_route_detail(self, s):
        dic_route_detail = {}

        for j in self.DIC_ROUTE_MESSAGE_REG:
            route_message = re.search(self.DIC_ROUTE_MESSAGE_REG[j], s)
            if route_message:
                dic_route_detail.update({j: route_message.group()})
        ad_metric0 = re.search(r'\[\d*/\d*\]', s)
        if ad_metric0:
            ad_metric = re.search(r'\d*/\d*', ad_metric0.group())
            if ad_metric:
                dic_route_detail.update({'AD/Metric': ad_metric.group()})
        next_hop0 = re.search(self.NEXT_HOP_REG, s)
        if next_hop0:
            next_hop = re.search(self.IP_REG, next_hop0.group())
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
        list_keys = ['Type', 'AD/Metric', 'Interface', 'NextHop']

        print('These are %d different routes.' % len(set_result_keys))
        for m in sorted(set_result_keys):
            print(64 * '-')
            print('%-18s' % m)
            for n in [0, 1]:
                list_s = [list_file_name[n], ' ']
                if m in list_dic_table[n]:
                    count = 0
                    length = len(list_dic_table[n][m])
                    j = len(list_file_name[n])
                    for l in list_dic_table[n][m]:
                        count += 1
                        for q in list_keys:
                            list_s.extend([' ', l[q] if l.get(q) else ''])
                        if count != length:
                            list_s.extend(['\n ', j*' '])
                print(''.join(list_s))
        print('\nThese are %d different routes.' % len(set_result_keys))
        return

    @staticmethod
    def show_result_table0(set_result_keys, list_file_name, list_dic_table):
        """输出结果表格上下对比"""
        list_keys = ['Type', 'AD/Metric', 'Interface', 'NextHop']
        pt = prettytable.PrettyTable()
        pt.field_names = ['Route', 'Table'] + list_keys
        pt.align = 'l'  # Left align city names
        result_file_name = '.\\' + list_file_name[0] + '_vs_' + list_file_name[1] + '.txt'

        with open(result_file_name, 'w') as f:
            for m in sorted(set_result_keys):
                count1 = 0
                for n in [0, 1]:
                    if m in list_dic_table[n]:
                        count2 = 0
                        for l in list_dic_table[n][m]:
                            row = [m if count1 == 0 else '', list_file_name[n] if count2 == 0 else '']
                            for q in list_keys:
                                row.append(l[q] if l.get(q) else '')
                            pt.add_row(row)
                            count1 += 1
                            count2 += 1
                    else:
                        pt.add_row([m if count1 == 0 else '', list_file_name[n], '', '', '', ''])
                        count1 += 1
                pt.add_row(6*['-'])
            f.write('These are %d different routes.\n' % len(set_result_keys))
            f.write(str(pt))
        os.system(result_file_name)
        return

    @staticmethod
    def show_result_table1(set_result_keys, list_file_name, list_dic_table):
        """输出结果表格左右对比"""
        list_keys = ['Type', 'AD/Metric', 'Interface', 'NextHop']
        list_keys0 = ['A Type', 'A AD/Metric', 'A Interface', 'A NextHop']
        list_keys1 = ['B Type', 'B AD/Metric', 'B Interface', 'B NextHop']
        pt = prettytable.PrettyTable()
        pt.field_names = list_keys0 + [list_file_name[0] + ' Route ' + list_file_name[1]] + list_keys1
        pt.align = 'l'                                          # Left align city names
        result_file_name = '.\\' + list_file_name[0] + '_vs_' + list_file_name[1] + '.txt'

        with open(result_file_name, 'w') as f:
            for m in sorted(set_result_keys):
                count1 = -1
                row_list = []
                if m in list_dic_table[0]:
                    for l in list_dic_table[0][m]:
                        # l like {'Type': 'R', 'Interface': 'FastEthernet1/1', 'AD/Metric': '120/1', 'NextHop': '192.168.2.66'}
                        count1 += 1
                        row_list.append([])
                        for q in list_keys:
                            row_list[count1].append(l[q] if l.get(q) else '')
                        row_list[count1].append(m if count1 == 0 else '')
                count2 = -1
                if m in list_dic_table[1]:
                    for l in list_dic_table[1][m]:
                        count2 += 1
                        if count2 > count1:
                            row_list.append([])
                            row_list[count2] = ['', '', '', '', m if count2 == 0 else '']
                        for q in list_keys:
                            row_list[count2].append(l[q] if l.get(q) else '')
                while count2 < count1:
                    count2 += 1
                    row_list[count2].extend(['', '', '', ''])
                for j in range(0, count2+1):
                    pt.add_row(row_list[j])
                pt.add_row(9*['------'])
            f.write('These are %d different routes.\n' % len(set_result_keys))
            f.write(str(pt))
        os.system(result_file_name)
        return

def main():
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
        RouteCompare.show_result_table1(RouteCompare.compare_route_table(list_dic_route_table), list_argv, list_dic_route_table)
    sys.exit()


if __name__ == '__main__':
    main()


