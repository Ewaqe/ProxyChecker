from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from asyncio import Semaphore, gather, get_event_loop, create_task
from typing import Optional
from dataclasses import dataclass
from loguru import logger
from getpass import getpass
import warnings


@dataclass(frozen=True)
class Proxy:
    type: str
    host: str
    port: int
    user: Optional[str] = None
    pswd: Optional[str] = None

    def url(self) -> str:
        if self.user != None:
            auth = self.user
            if self.pswd != None:
                auth += f':{self.pswd}@'
            else:
                auth += '@'
        else:
            auth = ''
        return f'{self.type}://{auth}{self.host}:{self.port}'

    def __str__(self) -> str:
        if self.user != None:
            auth = self.user
            if self.pswd != None:
                auth += f':{self.pswd}@'
            else:
                auth += '@'
        else:
            auth = ''
        return f'{self.host}:{self.port}{auth}'


sem = Semaphore(10)

async def check(proxy: Proxy):
    async with sem:
        try:
            async with ClientSession(connector=ProxyConnector.from_url(proxy.url())) as s:
                async with s.get('https://google.com/', timeout=5) as r:
                    logger.success(proxy.url())
                    return True, proxy
        except Exception as e:
            logger.error(proxy.url())
            return False, proxy


async def main():
    proxy_type = input('Enter proxy type(http/https/socks4/socks5): ')
    
    with open('base.txt', 'r', encoding='utf8') as f:
        proxies = set((Proxy(proxy_type, *l.replace('\n', '').split(' ')[0].split(':')) for l in f.readlines()))

    results = await gather(*[check(proxy) for proxy in proxies])

    good_count, bad_count = 0, 0

    with open('good.txt', 'w', encoding='utf8') as good_file:
        with open('bad.txt', 'w', encoding='utf8') as bad_file:
            for good, proxy in results:
                if good:
                    good_file.write(f'{proxy}\n')
                    good_count += 1
                else:
                    bad_file.write(f'{proxy}\n')
                    bad_count += 1

    logger.info(f'Goods {good_count}/{len(results)} - good.txt')
    logger.info(f'Bads {bad_count}/{len(results)} - bad.txt')
    

if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        get_event_loop().run_until_complete(main())
    except Exception as e:
        logger.exception(e)
    
    getpass('\n\nPress enter...')
