import random
from functools import lru_cache


class Mock(object):

    def __init__(self, max_num=None):
        self.max_num = max_num or 100

    @lru_cache(maxsize=16)
    def mock_ip_list(self):

        ip_pool = []
        for i in range(self.max_num):
            cur_ip = []
            for _ in range(4):
                ip_n = str(random.randint(1, 254))
                cur_ip.append(ip_n)

            ip_port = '.'.join(cur_ip) + f':{i + 1}'
            ip_pool.append(ip_port)
        return ip_pool


mock = Mock(max_num=100)
