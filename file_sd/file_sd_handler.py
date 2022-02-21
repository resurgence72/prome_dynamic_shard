import os
import re
from json import dump
from utils.logger import log
from pkg.ansibleAPI import MyAnsiable
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed


class FileSDHandler(object):

    def __init__(
            self,
            scrape_name,
            dest_sd_file_name,
            playbook_name
    ):
        abs_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        scrape_name = scrape_name.split('scrape_prome_')[1]
        self.file_sd_path = f'{abs_path}/file_sd/{scrape_name}'

        if not os.path.exists(self.file_sd_path):
            log.info("local sd dir {} create", self.file_sd_path)
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
                # TODO target node meta info
                'labels': {'env_name': 'test'}
            }]

            node_ip = node.split(':')[0]
            with open(
                    f'{self.file_sd_path}/{self.dest_sd_file_name}_{node_ip}.json',
                    'w'
            ) as f:
                dump(file_sd_targets, f)

    def async_distribute(self, target_ip, name):
        log.info("ansible async distribute {}--{}", target_ip, name)
        api = MyAnsiable(
            inventory=[target_ip],
            connection='smart',
            inventory_type='dynamic',
            # demo use pwd and root
            host_variables={'ansible_ssh_pass': 1, 'ansible_ssh_user': 'root'},
        )

        api.playbook(
            playbooks=[self.playbook_file, ],
            extra_vars={
                'src_sd_file_name': f'{self.file_sd_path}/{name}',
                'dest_sd_file_name': f'{self.dest_sd_file_name}.json',
            }
        )
        return api.get_result()

    def distribution(self, target_node_map):
        self.create_fd_files(target_node_map)

        re_matcher = re.compile(r'(([01]{0,1}\d{0,1}\d|2[0-4]\d|25[0-5])\.){3}([01]{0,1}\d{0,1}\d|2[0-4]\d|25[0-5])')

        with ThreadPoolExecutor(max_workers=5) as pool:
            tasks = []
            for _, _, files in os.walk(self.file_sd_path):
                for name in files:
                    if name.endswith('json'):
                        target_result = re.search(re_matcher, name)
                        if not target_result:
                            continue

                        target_ip = target_result.group()
                        tasks.append(pool.submit(self.async_distribute, target_ip, name))

            self.analysis_results(tasks)

    @staticmethod
    def analysis_results(tasks):
        task_result = defaultdict(list)
        for task in as_completed(tasks, timeout=15):
            data = task.result()
            for k, v in data.items():
                task_result[k].extend(v.keys())

        for distribute_status, host_list in task_result.items():
            log.debug(f'distribute_status: {distribute_status}, host_list: {host_list}')

            # TODO  alert distribute status
