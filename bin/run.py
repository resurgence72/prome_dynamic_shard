"""
1. shard启动后将prome节点注入consul，并且watch变化
2. shard 从cmdb拉取采集机器列表，一致性哈希分发至两台机器 file_sd 并且reload
3. 当watch变化后，重新计算一致性哈希并重新分发file_sd且reload
"""
import time

from pkg.consulAPI import ConsulAPI
from config.config import loader
from collections import defaultdict
from threading import Thread
from common.common import que
from file_sd.file_handler import FileSDHandler
from utils.util import get_ecs_list_from_cmdb
from pkg.consistent_hash import ConsistentHash


def get_consistent_hash_map(prome_nodes):
    target_node_map = defaultdict(list)

    hash_ring = ConsistentHash(replicas=300, nodes=prome_nodes)

    # get target node
    for ecs in get_ecs_list_from_cmdb():
        target_node = hash_ring.get_node(ecs)
        target_node_map[target_node].append(ecs)
    return target_node_map


def Run():
    # 1. shard启动后将prome节点注入consul，并且watch变化
    consul_conf = loader.get_consul_config()
    consul_svc_name = consul_conf.get('consul_service_name')

    consul_host, consul_port = consul_conf.get('host'), consul_conf.get('port')
    client = ConsulAPI(consul_host, consul_port)

    scrape_map = loader.get_shard_service()

    for scrape_name, scrape in scrape_map.items():
        scrape_name = scrape_name.split('scrape_prome_')[1]
        prome_nodes = scrape.get('prome_nodes')

        # register prome to consul
        for idx, node in enumerate(prome_nodes, start=1):
            node_host, node_port = node.split(':')[0], int(node.split(':')[1])
            client.register_service(
                consul_svc_name,
                consul_svc_name + f'_{idx}',
                node_host,
                node_port,
                tags=['test'],
                # deregister=10,
            )

        dest_sd_file_name = scrape.get('dest_sd_file_name')
        playbook_name = scrape.get('playbook_name')
        sync_distribute(scrape_name, prome_nodes, dest_sd_file_name, playbook_name)

        # 3. 当watch变化
        wait_interval = loader.get_job_config().get('ticker_interval')

        thread_list = []
        prome_watchDog = Thread(target=watch_prome_change, args=(client, consul_svc_name, wait_interval))
        thread_list.append(prome_watchDog)

        # when que has list
        try_loop_watchDog = Thread(target=try_loop, args=(scrape_name, dest_sd_file_name, playbook_name))
        thread_list.append(try_loop_watchDog)

        for thread in thread_list:
            thread.start()


def watch_prome_change(client, service_name, interval):
    client.watch_service(service_name, interval)


def sync_distribute(scrape_name, prome_nodes, dest_sd_file_name, playbook_name):
    target_node_map = get_consistent_hash_map(prome_nodes)
    # create file_sd json and distribution to remote prome host

    for k, v in target_node_map.items():
        print("sync_distribute start: ", k, len(v))

    f_sd = FileSDHandler(scrape_name, dest_sd_file_name, playbook_name)
    f_sd.distribution(target_node_map)


def try_loop(scrape_name, dest_sd_file_name, playbook_name):
    while 1:
        print('wait que')
        if que.empty():
            time.sleep(2)
            continue

        prome_nodes = que.get(timeout=5)

        if prome_nodes:
            print('que result: ', prome_nodes)
            # re distrubute
            sync_distribute(scrape_name, prome_nodes, dest_sd_file_name, playbook_name)
