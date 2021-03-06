#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

try:
    # py2
    from urllib2 import urlopen
    from urllib2 import Request
    from urllib import urlencode
except ImportError:
    # py3
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode

import time
import os
import json
import argparse

GUESS = 'http://m.kuaidi100.com/autonumber/auto?{0}'
QUERY = 'http://m.kuaidi100.com/query?{0}'

HISTORY = os.path.join(os.path.expanduser('~'), '.kd100')


def save(data):
    with open(HISTORY, 'wb') as f:
        f.write(json.dumps(data, f, ensure_ascii=False, indent=2).encode('utf-8'))


def load():
    try:
        with open(HISTORY) as f:
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
    if not r:
        return
    r['label'] = label
    show(r, True)
    # print(r['nu'], r['label'], r['data'][0]['time'], r['data'][0]['context'])

    history = load()
    history[r['nu']] = r
    save(history)


def format_info(data):
    res = 'code: {nu: <20} label: {label:<10} company: {com: <15} ' \
          'is checked: {ischeck}\n'.format(**data)
    res += '=' * 75 + '\n'
    res += '{0: ^21}|{1: ^44}\n'.format('time', 'content')
    for item in data['data']:
        res += '-' * 75 + '\n'
        res += '{time: ^21}| {context}\n'.format(**item)
    res += '=' * 75 + '\n'
    return res


def show(record, detail=False):
    if detail:
        print(format_info(record))
    else:
        print('{nu:<20} {label:<10} {com:<15} {data[0][time]:^21} {data[0][context]:^44}'.format(**record))


def refresh():
    history = load()

    new_status = {}
    for code, record in history.items():

        # 快递单当前的状态 :
        # 0：在途，即货物处于运输过程中；
        # 1：揽件，货物已由快递公司揽收并且产生了第一条跟踪信息；
        # 2：疑难，货物寄送过程出了问题；
        # 3：签收，收件人已签收；
        # 4：退签，即货物由于用户拒签、超区等原因退回，而且发件人已经签收；
        # 5：派件，即快递正在进行同城派件；
        # 6：退回，货物正处于退回发件人的途中；
        if record['state'] in ['3', '4']:
            continue

        r = kd100_query(code, company=record['com'])
        r['label'] = record.setdefault('label', '')
        new_status[code] = r
        time.sleep(1)

    save(new_status)
    return new_status


def kd100_query(code, quite=None, company=None):
    params = urlencode({'num': code})
    guess_url = GUESS.format(params)

    if company is None:
        res = json.loads(urlopen(guess_url).read().decode('utf-8'))
        possible_company_name = [company['comCode'] for company in res]
    else:
        possible_company_name = [str(company)]

    if not quite:
        print('Possible company:', ', '.join(possible_company_name))

    for company_name in possible_company_name:
        if not quite:
            print('Try', company_name, '...', end='')

        params = urlencode({
            'type': company_name,
            'postid': code,
        })

        req = Request(QUERY.format(params), headers={'Referer': guess_url})
        res = json.loads(urlopen(req).read().decode('utf-8'))

        if res['message'] == 'ok':
            if not quite:
                print('Done.\n')
            return res
        else:
            if not quite:
                print('Failed.')
    else:
        print('\nNo results.')
        return None


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
    parser.add_argument('-q', '--quite',
                        help='be quite',
                        action='store_true',
                        default=False)
    args = parser.parse_args()

    if args.code:
        add_query(args.code, args.company, args.label)
        return

    data = refresh()
    print('Latest status:')
    for record in data.values():
        show(record, args.detail)


if __name__ == '__main__':
    main()
