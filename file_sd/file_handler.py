import os
import re
from json import dump
from common.common import lock
from pkg.ansibleAPI import MyAnsiable


class FileSDHandler(object):

    def __init__(self, scrape_name, dest_sd_file_name, playbook_name):
        abs_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.file_sd_path = f'{abs_path}/file_sd/{scrape_name}'

        if not os.path.exists(self.file_sd_path):
            os.mkdir(self.file_sd_path)

        self.scrape_name = scrape_name
        self.dest_sd_file_name = dest_sd_file_name.split('.')[0]
        self.playbook_file = f'{abs_path}/ansible_yml/{playbook_name}'

    def create_fd_files(self, target_map):
        for _, _, files in os.walk(self.file_sd_path):
            for name in files:
                if name.endswith('json'):
                    os.remove(f'{self.file_sd_path}/{name}')

        for node, targets in target_map.items():
            file_sd_targets = [{
                'targets': targets,
                'labels': {'env_name': 'test'}
            }]

            node = node.split(':')[0]
            f = open(f'{self.file_sd_path}/{self.dest_sd_file_name}_{node}.json', 'w')
            dump(file_sd_targets, f)
            f.close()

    def distribution(self, target_node_map):
        self.create_fd_files(target_node_map)

        re_matcher = re.compile(r'(([01]{0,1}\d{0,1}\d|2[0-4]\d|25[0-5])\.){3}([01]{0,1}\d{0,1}\d|2[0-4]\d|25[0-5])')
        for _, _, files in os.walk(self.file_sd_path):
            for name in files:
                if name.endswith('json'):
                    target_result = re.search(re_matcher, name)
                    if not target_result:
                        continue

                    target_ip = target_result.group()

                    lock.acquire(timeout=15)
                    api = MyAnsiable(
                        inventory=[target_ip],
                        connection='smart',
                        inventory_type='dynamic',
                        host_variables={'ansible_ssh_pass': 1, 'ansible_ssh_user': 'root'},
                    )

                    api.playbook(
                        playbooks=[self.playbook_file],
                        extra_vars={
                            'src_sd_file_name': f'{self.file_sd_path}/{name}',
                            'dest_sd_file_name': f'{self.dest_sd_file_name}.json',
                        }
                    )
                    lock.release()
