# coding: utf-8

import aiohttp
import asyncio

import argparse
import collections
import datetime
import json
import re
import subprocess


async def get_ip_data(ip):
    API_URL = 'http://ip-api.com/json/{}'
    async with aiohttp.get(API_URL.format(ip)) as r:
        data = await r.json()
        return data


async def travel2(destination, timeout=23):
    ip_pattern = re.compile('\(([\d\.]+)\)')
    process = subprocess.Popen(
        ['traceroute', destination],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    travel_path = collections.OrderedDict()
    start = datetime.datetime.now()

    while (datetime.datetime.now() - start).seconds < timeout:
        await asyncio.sleep(1)
        line = process.stdout.readline().strip()
        if line == '' and process.poll() is not None:
            break

        if line:
            match = ip_pattern.search(str(line))
            if not match:
                continue

            ip_address = match.group(1)
            travel_path[ip_address] = None

            data = await get_ip_data(ip_address)
            if data['status'] == 'fail':
                continue

            travel_path[ip_address] = ', '.join([
                data['city'], data['country']
            ])

    city_list = [None]
    for city in travel_path.values():
        if city and city_list[-1] != city:
            city_list.append(city)

    return city_list[1:]


async def main(destination):
    print(
        'In order to get to "{}" '
        'your packets have to travel to:'.format(destination)
    )
    city_list = await travel2(destination)
    if city_list:
        for city in city_list:
            print(city)
    else:
        print('the Moon')

if __name__ == '__main__':
    description = 'Find out the way to get to your site!'

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('destination')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.destination))
