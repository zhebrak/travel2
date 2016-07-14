# coding: utf-8

import aiohttp
import argparse
import asyncio
import re
import sys

# pattern to find ip address in traceroute output
ip_pattern = re.compile('\(([\d\.]+)\)')


async def get_ip_data(ip, session):
    with aiohttp.Timeout(10):
        async with session.get('http://ip-api.com/json/{}'.format(ip)) as r:
            assert r.status == 200
            return await r.json()


async def travel2(session, destination):
    process = await asyncio.create_subprocess_exec(
        "traceroute", destination,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    while True:
        line = await process.stdout.readline()
        if not line:
            break

        line = line.strip()

        match = ip_pattern.search(str(line))
        if not match:
            continue

        ip_address = match.group(1)

        data = await get_ip_data(ip_address, session)
        if data['status'] == 'fail':
            out = "{}: {}".format(line.decode("utf-8"), data["message"])
        else:
            out = "{}: {}, {}".format(line.decode("utf-8"), data['city'], data['country'])

        print(out)

    await process.wait()


def main():
    description = 'Find out the way to get to your site!'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('destination')
    parser.add_argument("--timeout", help="timeout", default=30, type=int, dest="timeout")
    args = parser.parse_args()
    
    print(
        'In order to get to "{}" '
        'your packets have to travel to:'.format(args.destination)
    )
    
    loop = asyncio.get_event_loop()
    session = aiohttp.ClientSession()
    
    try:
        loop.run_until_complete(asyncio.wait_for(travel2(session, args.destination), timeout=args.timeout))
    except KeyboardInterrupt:
        print("interrupted")
        sys.exit(1)
    except asyncio.TimeoutError:
        print("timed out")
        sys.exit(1)
    else:
        loop.close()
    finally:
        session.close()


if __name__ == '__main__':
    main()
