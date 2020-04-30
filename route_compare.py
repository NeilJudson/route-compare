# -*- coding: utf-8 -*-

import copy
import os
import re

import chardet
import prettytable


def get_route_table(route_os, file_name):
    if 'IOS' == route_os:
        return get_route_table_ios(file_name)
    elif 'NXOS' == route_os:
        return get_route_table_nxos(file_name)
    elif 'H3C' == route_os:
        return
    elif 'HUAWEI' == route_os:
        return


# ==========================================================================
# IOS
# ==========================================================================
def get_route_table_ios(file_name):
    """Get route table.

    :return:
        dict route_table: A dict of route table. For example:
            {
                "192.168.0.0/24": {  # route
                    "192.168.1.1": {  # NextHop
                        "Interface": "TenGigabitEthernet1/1",
                        "AD/Metric": "90/1024",
                        "Type": "D"
                    }
                }
            }
    """

    with open(file_name, 'rb') as f:
        s = f.read()
        encode_type = chardet.detect(s)['encoding']
    with open(file_name, encoding=encode_type) as f:
        s = f.read()

    route_entry_reg = re.compile(
        r'(([LCSRMBDOi](?:[* ]{1,2}(?:EX|IA|N1|N2|E1|E2|su|L1|L2|ia))?) +([\d.]+(?:/\d+)?)\s+'
        r'(?:(?:is directly connected|is a summary|\[\d+/\d+\] via [\d.]+).+\s*)+)'
    )

    path_entry_reg = re.compile(
        r'((is directly connected|is a summary|\[(\d+/\d+)\] via ([\d.]+)).+?'
        r'((?:Hu|Fo|Te|Gi|Fa|Eth|Se|Lo|Po|Vlan|Null)\D*[\d/.:]+)?\s*)'
    )

    route_table = {}

    result = re.findall(route_entry_reg, s)
    if result:
        for m in result:
            type = m[1]
            route = m[2]
            result1 = re.findall(path_entry_reg, m[0])
            path = {}
            for n in result1:
                nexthop = n[3]
                if nexthop:
                    pass
                else:
                    nexthop = n[1]
                path.update({nexthop: {'Interface': n[4], 'AD/Metric': n[2], 'Type': type}})
            route_table.update({route: path})
        return route_table
    else:
        raise Exception('Unexpected file: {}'.format(file_name))


# ==========================================================================
# NX-OS
# ==========================================================================
def get_route_table_nxos(file_name):
    """Get route table.

    :return:
        dict route_table: A dict of route table. For example:
            {
                "192.168.0.0/24": {  # route
                    "192.168.1.1": {  # NextHop
                        "Interface": "Eth3/9",
                        "AD/Metric": "90/1024",
                        "Type": "eigrp-eigrp-core, external, tag 3"
                    }
                }
            }
    """

    with open(file_name, 'rb') as f:
        s = f.read()
        encode_type = chardet.detect(s)['encoding']
    with open(file_name, encoding=encode_type) as f:
        s = f.read()

    route_entry_reg = re.compile(
        r'(([\d.]+/\d+).+\s+'
        r'(.+via (?:[\d.]+, )?(?:Te|Gi|Fa|Eth|Lo|Vlan|Po|Null)\D*[\d/.:]+, \[\d+/\d+\].+\s*)+)'
    )
    path_entry_reg = re.compile(
        r'(.+via (?:([\d.]+), )?((?:Te|Gi|Fa|Eth|Lo|Vlan|Po|Null)\D*[\d/.:]+), \[(\d+/\d+)\].+((?:ospf|eigrp|static|direct|local|hsrp).*?)\s*)'
    )

    route_table = {}

    result = re.findall(route_entry_reg, s)
    if result:
        for m in result:
            route = m[1]
            result1 = re.findall(path_entry_reg, m[0])
            path = {}
            for n in result1:
                path.update({n[1]: {'Interface': n[2], 'AD/Metric': n[3], 'Type': n[4]}})
            route_table.update({route: path})
        return route_table
    else:
        raise Exception('Unexpected file: {}'.format(file_name))


# ==========================================================================
# H3C
# ==========================================================================


# ==========================================================================
# HUAWEI
# ==========================================================================


def compare_route_table(route_table_old, route_table_new):
    """比较两个格式化后的日志结果
    :param route_table_old:
    :param route_table_new:
    :return:
    """
    if route_table_old == route_table_new:
        print('These two route tables are the same.')
        return {}
    else:
        print('These two route tables are different.')

    result_add = {}
    result_del = {}
    result_edit = {}

    route_table_old_keys = route_table_old.keys()
    route_table_new_keys = route_table_new.keys()

    route_table_add_keys = route_table_new_keys - route_table_old_keys
    route_table_del_keys = route_table_old_keys - route_table_new_keys
    route_table_mul_keys = route_table_old_keys & route_table_new_keys

    route_table_edit_keys = copy.copy(route_table_mul_keys)
    for route in route_table_mul_keys:
        # delete the same item
        if route_table_old[route] == route_table_new[route]:
            route_table_edit_keys.remove(route)

    for route in route_table_add_keys:
        result_add.update({
            route: [
                {
                    'Old NextHop': '', 'Old AD/Metric': '', 'Old Interface': '', 'Old Type': '',
                    'New NextHop': nexthop,
                    'New AD/Metric': route_table_new[route][nexthop]['AD/Metric'],
                    'New Interface': route_table_new[route][nexthop]['Interface'],
                    'New Type': route_table_new[route][nexthop]['Type']
                } for nexthop in route_table_new[route]
            ]
        })

    for route in route_table_del_keys:
        result_del.update({
            route: [
                {
                    'Old NextHop': nexthop,
                    'Old AD/Metric': route_table_old[route][nexthop]['AD/Metric'],
                    'Old Interface': route_table_old[route][nexthop]['Interface'],
                    'Old Type': route_table_old[route][nexthop]['Type'],
                    'New NextHop': '', 'New AD/Metric': '', 'New Interface': '', 'New Type': ''
                } for nexthop in route_table_old[route]
            ]
        })

    for route in route_table_edit_keys:
        l = []
        for nexthop in route_table_new[route]:
            if nexthop in route_table_old[route]:
                l.append({
                    'Old NextHop': nexthop,
                    'Old AD/Metric': route_table_old[route][nexthop]['AD/Metric'],
                    'Old Interface': route_table_old[route][nexthop]['Interface'],
                    'Old Type': route_table_old[route][nexthop]['Type'],
                    'New NextHop': nexthop,
                    'New AD/Metric': route_table_new[route][nexthop]['AD/Metric'],
                    'New Interface': route_table_new[route][nexthop]['Interface'],
                    'New Type': route_table_new[route][nexthop]['Type']
                })
            else:
                l.append({
                    'Old NextHop': '', 'Old AD/Metric': '', 'Old Interface': '', 'Old Type': '',
                    'New NextHop': nexthop,
                    'New AD/Metric': route_table_new[route][nexthop]['AD/Metric'],
                    'New Interface': route_table_new[route][nexthop]['Interface'],
                    'New Type': route_table_new[route][nexthop]['Type']
                })
        for nexthop in route_table_old[route].keys() - route_table_new[route].keys():
            l.append({
                'Old NextHop': nexthop,
                'Old AD/Metric': route_table_old[route][nexthop]['AD/Metric'],
                'Old Interface': route_table_old[route][nexthop]['Interface'],
                'Old Type': route_table_old[route][nexthop]['Type'],
                'New NextHop': '', 'New AD/Metric': '', 'New Interface': '', 'New Type': ''
            })
        result_edit.update({route: l})

    return {'add': result_add, 'del': result_del, 'edit': result_edit}


def show_result_table(result, file_name_old, file_name_new):
    """用prettytable展现对比结果

    :param result:
    :param file_name_old:
    :param file_name_new:
    :return:
    """

    result_add = result['add']
    result_del = result['del']
    result_edit = result['edit']

    list_keys1 = ['Old Type', 'Old AD/Metric', 'Old Interface', 'Old NextHop']
    list_keys2 = ['New Type', 'New AD/Metric', 'New Interface', 'New NextHop']
    pt = prettytable.PrettyTable()
    pt.field_names = list_keys1 + [file_name_old + ' Route ' + file_name_new] + list_keys2
    pt.align = 'l'  # Left align city names
    result_file_name = '.\\' + file_name_old + '_vs_' + file_name_new + '.txt'

    pt.add_row(['新增', '', '', '', '', '', '', '', ''])
    pt.add_row(9 * ['------'])
    for route in sorted(result_add.keys()):
        for i in result_add[route]:
            pt.add_row([i[x] for x in list_keys1] + [route] + [i[y] for y in list_keys2])
        pt.add_row(9 * ['------'])

    pt.add_row(['删除', '', '', '', '', '', '', '', ''])
    pt.add_row(9 * ['------'])
    for route in sorted(result_del.keys()):
        for i in result_del[route]:
            pt.add_row([i[x] for x in list_keys1] + [route] + [i[y] for y in list_keys2])
        pt.add_row(9 * ['------'])

    pt.add_row(['修改', '', '', '', '', '', '', '', ''])
    pt.add_row(9 * ['------'])
    for route in sorted(result_edit.keys()):
        for i in result_edit[route]:
            pt.add_row([i[x] for x in list_keys1] + [route] + [i[y] for y in list_keys2])
        pt.add_row(9 * ['------'])

    with open(result_file_name, 'w') as f:
        f.write(str(pt))
    os.system(result_file_name)

    return


def result_to_web(result):
    """对比结果转换成web接口数据格式

    :param result:
    :return:
    """

    result_add = result['add']
    result_del = result['del']
    result_edit = result['edit']

    items_add = []
    items_del = []
    items_edit = []

    for route in result_add:
        key = route
        for l in result_add[route]:
            items_add.append({
                'Old_Type': l['Old Type'],
                'Old_AD_Metric': l['Old AD/Metric'],
                'Old_Interface': l['Old Interface'],
                'Old_NextHop': l['Old NextHop'],
                'key': key,
                'New_Type': l['New Type'],
                'New_AD_Metric': l['New AD/Metric'],
                'New_Interface': l['New Interface'],
                'New_NextHop': l['New NextHop']
            })
            key = ''

    for route in result_del:
        key = route
        for l in result_del[route]:
            items_del.append({
                'Old_Type': l['Old Type'],
                'Old_AD_Metric': l['Old AD/Metric'],
                'Old_Interface': l['Old Interface'],
                'Old_NextHop': l['Old NextHop'],
                'key': key,
                'New_Type': l['New Type'],
                'New_AD_Metric': l['New AD/Metric'],
                'New_Interface': l['New Interface'],
                'New_NextHop': l['New NextHop']
            })
            key = ''

    for route in result_edit:
        key = route
        for l in result_edit[route]:
            items_edit.append({
                'Old_Type': l['Old Type'],
                'Old_AD_Metric': l['Old AD/Metric'],
                'Old_Interface': l['Old Interface'],
                'Old_NextHop': l['Old NextHop'],
                'key': key,
                'New_Type': l['New Type'],
                'New_AD_Metric': l['New AD/Metric'],
                'New_Interface': l['New Interface'],
                'New_NextHop': l['New NextHop']
            })
            key = ''

    return {'items_add': items_add, 'items_del': items_del, 'items_edit': items_edit}


# if __name__ == '__main__':
#     path = '/Users/fanhaimu/workspace/py_api/RouteCompare/doc/test/NXOS/'
#     file1 = 'show_ip_route_AF.txt'
#     file2 = 'show_ip_route_BF.txt'
#     route_os = 'NXOS'
#
#     route_table_old = get_route_table(route_os, path + file1)
#     route_table_new = get_route_table(route_os, path + file2)
#     result = compare_route_table(route_table_old, route_table_new)
#     print(result_to_web(result))
