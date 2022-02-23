import consul
from common.common import com
from collections import namedtuple


class ConsulAPI(object):

    def __init__(self, host, port):
        self._consul = consul.Consul(host, port)

    def register_service(
            self,
            s_name,
            s_id,
            host,
            port,
            tags=None,
            deregister=None
    ):

        tags = tags or []

        self._consul.agent.service.register(
            name=s_name,
            service_id=s_id,
            address=host,
            port=port,
            tags=tags,
            # 健康检查ip端口，检查时间：5,超时时间：30，注销时间：30s
            check=consul.Check().tcp(host, port, "5s", "5s", deregister=deregister)
        )

    def deregister_services(self, services_id):
        """
        取消注册
        :param services_id:
        :return:
        """
        if not isinstance(services_id, (list, tuple)):
            services_id = [services_id]

        for service_id in services_id:
            self._consul.agent.service.deregister(service_id=service_id)

    def get_service(self, name):
        """
        获取服务信息
        :param name:
        :return:
        """
        services = self._consul.agent.services()
        service = services.get(name)

        SR = namedtuple('service_result', ['service', 'addr'])
        if not service:
            return SR(None, None)
        addr = "{0}:{1}".format(service['Address'], service['Port'])
        return SR(service, addr)

    def set_KV(self, k, v):
        """
        设置 kv
        :param k:
        :param v:
        :return:
        """
        self._consul.kv.put(k, v)

    def async_get_KV(self, k):
        """
        获取 kv
        :param k:
        :return:
        """
        idx, v = self._consul.kv.get(k)
        KVR = namedtuple('kv_result', ['idx', 'v'])
        if not v:
            return KVR(idx, None)

        return KVR(idx, v.get('Value'))

    def sync_get_KV(self, k, idx):
        """
        同步模式获取kv
        使用index 作为参数会阻塞住请求, 直到有数据更新或者超时
        :param k:
        :param idx:
        :return:
        """
        idx, v = self._consul.kv.get(k, index=idx)
        KVR = namedtuple('kv_result', ['idx', 'v'])
        if not v:
            return KVR(idx, None)

        return KVR(idx, v.get('Value'))

    def get_health_services(self, service):
        # set passing=true filter unhealthy node
        _, v = self._consul.health.service(service, passing=True)
        tmp = []

        for vv in v:
            print(vv, end='\n\n')
            service = vv.get('Service')
            ip = service.get('Address')
            port = service.get('Port')
            tmp.append(f'{ip}:{port}')
        return tmp

    def watch_service(self, service, interval):
        idx, last_idx = None, None

        while 1:
            last_idx = idx
            idx, data = self._consul.health.service(
                service,
                passing=True,
                wait=f'{interval}s',
                index=idx
            )

            if not last_idx or last_idx == idx:
                continue

            nodes = []
            for i, d in enumerate(data):
                svc = d.get('Service')
                addr = svc.get('Address')
                # id = svc.get('ID')
                if addr:
                    nodes.append(addr)

            com.que.put(nodes)


if __name__ == '__main__':
    api = ConsulAPI(host="10.0.0.112", port=8500)
    # api.deregister_services(["prome_nodes_2", "prome_nodes_1", "prome_nodes_0"])
    print(api.get_health_services('scrape_prome_kafka'))
