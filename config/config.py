import os
import yaml


class ConfigLoader(object):

    def __init__(self):
        abs_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(f'{abs_path}/prome_shard.yml', encoding='utf8') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

    def get_shard_service(self):
        return self.config.get('shard_service')

    def get_job_config(self):
        return self.config.get('job_interval_config')

    def get_consul_config(self):
        return self.config.get('consul_config')


loader = ConfigLoader()
