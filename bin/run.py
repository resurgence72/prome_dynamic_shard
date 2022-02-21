"""
1. shard启动后将prome节点注入consul，并且watch变化
2. shard 从cmdb拉取采集机器列表，一致性哈希分发至两台机器 file_sd 并且reload
3. 当watch变化后，重新计算一致性哈希并重新分发file_sd且reload
"""
import time
from threading import Thread
from collections import defaultdict

from common.common import com
from config.config import loader
from utils.logger import log
from utils.dispatch import dispatch
from pkg.consulAPI import ConsulAPI
from file_sd.file_sd_handler import FileSDHandler
from pkg.consistent_hash import ConsistentHash


def get_consistent_hash_map(scrape_name, prome_nodes):
    target_node_map = defaultdict(list)

    hash_ring = ConsistentHash(replicas=300, nodes=prome_nodes)

    # fanshe get target node list
    if not hasattr(dispatch, scrape_name):
        log.error("scrape_name {} not implementation", scrape_name)
        assert Exception('scrape_name: ', scrape_name, 'not implementation')

    for ecs in getattr(dispatch, scrape_name)():
        target_node = hash_ring.get_node(ecs)
        target_node_map[target_node].append(ecs)
    return target_node_map


def Run():
    # 1. shard启动后将prome节点注入consul，并且watch变化
    consul_conf = loader.get_consul_config()
    consul_svc_name = consul_conf.get('consul_service_name')

    client = ConsulAPI(
        consul_conf.get('host'),
        consul_conf.get('port')
    )

    scrape_map = loader.get_shard_service()

    for scrape_name, scrape in scrape_map.items():
        prome_nodes = scrape.get('prome_nodes')

        # register prome to consul
        for idx, node in enumerate(
                prome_nodes,
                start=1
        ):
            node_host, node_port = node.split(':')[0], int(node.split(':')[1])
            client.register_service(
                consul_svc_name,
                consul_svc_name + f'_{idx}',
                node_host,
                node_port,
                # TODO consul tags
                tags=['test'],
                # deregister=10,
            )

        sync_distribute(
            scrape_name,
            prome_nodes,
            scrape.get('dest_sd_file_name'),
            scrape.get('playbook_name')
        )

    # 3. 当watch变化
    wait_interval = loader.get_job_config().get('ticker_interval')
    Thread(
        target=client.watch_service,
        args=(consul_svc_name, wait_interval)
    ).start()

    # when que has list
    Thread(target=try_loop, args=(scrape_map,)).start()


def sync_distribute(
        scrape_name,
        prome_nodes,
        dest_sd_file_name,
        playbook_name
):
    target_node_map = get_consistent_hash_map(scrape_name, prome_nodes)

    log.info('{} begin distribute', scrape_name)
    for k, v in target_node_map.items():
        log.info('sync distribute result: {} {}', k, len(v))
    log.info('{} end distribute\n', scrape_name)

    f_sd = FileSDHandler(
        scrape_name,
        dest_sd_file_name,
        playbook_name
    )
    # create file_sd json and distribution to remote prome host
    f_sd.distribution(target_node_map)


def try_loop(scrape_map):
    while 1:
        if com.que.empty():
            time.sleep(2)
            continue

        prome_nodes = com.que.get(timeout=5)
        if prome_nodes:
            log.info("queue get result, prome_nodes: {} ", prome_nodes)

            # sync distribute
            begin_distribute = time.time()
            for scrape_name, scrape in scrape_map.items():
                sync_distribute(
                    scrape_name,
                    prome_nodes,
                    scrape.get('dest_sd_file_name'),
                    scrape.get('playbook_name')
                )
            log.info("loop sync_distribute times: {} s", time.time() - begin_distribute)
