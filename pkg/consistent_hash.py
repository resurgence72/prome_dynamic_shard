import mmh3


class ConsistentHash(object):

    def __init__(self, replicas=3, nodes=None):
        self.replicas = replicas
        self.hash_ring = dict()
        self.sorted_keys = list()

        if nodes:
            for node in nodes:
                self.add_node(node)
        # self.nodes = nodes

    def add_node(self, node):
        for replica in range(self.replicas):
            # 通过虚拟节点获取 hash_sum
            key = self.gen_key(f'{node}#{replica}')
            # print(replica, key)
            self.hash_ring[key] = node
            # print(len(self.hash_ring))
            self.sorted_keys.append(key)

        # 对 hash_sum 排序
        self.sorted_keys.sort()

    def remove_node(self, node):
        for replica in range(self.replicas):
            key = self.gen_key(f'{node}#{replica}')
            del self.hash_ring[key]
            self.sorted_keys.remove(key)

    def get_node(self, key):
        return self.get_node_pos(key)

    def get_node_pos(self, key):
        if not self.hash_ring:
            print('not hash_ring and return None: ', self.hash_ring)
            return None

        gen_key = self.gen_key(key)
        node = self.binary_search_gen_key(gen_key)
        return self.hash_ring[node]

        # for node in self.sorted_keys:
        #     if key <= node:
        #         # print(node, self.hash_ring[node])
        #         return self.hash_ring[node]

    def binary_search_gen_key(self, target_key):
        left = 0
        right = len(self.sorted_keys) - 1

        while left <= right:
            mid = (left + right) // 2
            if self.sorted_keys[mid] == target_key:
                # 别返回，锁定左侧边界
                return self.sorted_keys[mid]
            elif self.sorted_keys[mid] < target_key:
                left = mid + 1
            elif self.sorted_keys[mid] > target_key:
                right = mid - 1

        # 最后要检查 left 越界的情况
        return self.sorted_keys[left]

    @staticmethod
    def gen_key(key):
        return mmh3.hash(key, 32, signed=False)
