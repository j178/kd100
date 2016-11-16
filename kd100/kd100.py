#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import time

try:
    # py2
    from urllib2 import urlopen
    from urllib2 import Request
    from urllib import urlencode
except ImportError:
    # py3
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode

import os
import json
import random
import argparse

GUESS = 'http://m.kuaidi100.com/autonumber/auto?{0}'
QUERY = 'http://m.kuaidi100.com/query?{0}'

HISTORY = os.path.join(os.path.expanduser('~'), '.kd100')


def save(data):
    with open(HISTORY, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def load():
    try:
        with open(HISTORY, encoding='utf-8') as f:
            j = json.load(f)
            return j if isinstance(j, dict) else {}
    except:
        return {}


def add_query(code, company=None, label=None):
    """
    添加快递运单
    :param code: 运单编号
    :param company: 快递公司
    :param label: 标签
    """

    r = kd100_query(code, company=company)
    r['label'] = label
    print(r['nu'], r['label'], r['data'][0]['time'], r['data'][0]['context'])

    history = load()
    history.setdefault(r['nu'], r)
    save(history)


def format_info(data):
    res = 'code: {nu: <20} label: {label: <10} company: {com: <15} ' \
          'is checked: {ischeck}\n'.format(**data)
    res += '=' * 75 + '\n'
    res += '{0: ^21}|{1: ^44}\n'.format('time', 'content')
    for item in data['data']:
        res += '-' * 75 + '\n'
        res += '{time: ^21}| {context}\n'.format(**item)
    res += '=' * 65 + '\n'
    return res


def show(data, detail=False):
    if detail:
        for record in data.values():
            print(format_info(record))
        return

    for record in data.values():
        print(record['nu'], record['label'], record['data'][0]['time'], record['data'][0]['context'])


def refresh():
    history = load()

    res = {}
    # todo may be not compatiable with PY2
    for code, record in history.items():
        r = kd100_query(code, company=record['com'])
        r.setdefault('label', record.setdefault('label', ''))
        time.sleep(1)

        if r['ischeck'] == '0':
            res.setdefault(code, r)

    save(res)
    return res


def kd100_query(code, company=None):
    params = urlencode({'num': code})
    guess_url = GUESS.format(params)

    if company is None:
        res = json.loads(urlopen(guess_url).read().decode('utf-8'))
        possible_company_name = [company['comCode'] for company in res]
    else:
        possible_company_name = [str(company)]

    # if not quite:
    #     print('Possible company:', ', '.join(possible_company_name))

    for company_name in possible_company_name:
        # if not quite:
        #     print('Try', company_name, '...', end='')

        params = urlencode({
            'type': company_name,
            'postid': code,
            'id': 1,
            'valicode': '',
            'temp': random.random()
        })

        req = Request(QUERY.format(params), headers={'Referer': guess_url})
        res = json.loads(urlopen(req).read().decode('utf-8'))

        if res['message'] == 'ok':
            # if not quite:
            #     print('Done.\n')
            return res

            # table = format_info(res)
            # if output:
            #     with open(output, 'wb') as f:
            #         f.write(table.encode('utf-8'))
            #     if not quite:
            #         print('Result saved to [' + os.path.abspath(output) + '].')
            # else:
            #     print(table)
            # break
            # else:
            #     if not quite:
            #         print('Failed.')
            # else:
            #     print('\nNo results.')


def main():
    parser = argparse.ArgumentParser(
            description="query express info use kuaidi100 api")
    parser.add_argument('-c', '--code', type=str, help='express code')
    parser.add_argument('-p', '--company', type=str,
                        help='express company, will auto '
                             'guess company if not provided',
                        default=None)
    parser.add_argument('-l', '--label', type=str,
                        help='label the express package', default='')
    parser.add_argument('-d', '--detail', action='store_true',
                        help='show express detail',
                        default=False)
    # parser.add_argument('-o', '--output', help='output file')
    # parser.add_argument('-q', '--quite',
    #                     help='be quite',
    #                     action='store_true',
    #                     default=False)
    args = parser.parse_args()

    if args.code:
        add_query(args.code, args.company, args.label)
        return

    data = refresh()
    show(data, args.detail)
    # express_code = args.code
    # if express_code is None:
    #     while True:
    #         try:
    #             express_code = input(
    #                     'Input your express code: ' if not args.quite else '')
    #             break
    #         except ValueError:
    #             if not args.quite:
    #                 print('Please input a number')

    # kd100_query(express_code, args.output, args.quite, args.company)


if __name__ == '__main__':
    main()
