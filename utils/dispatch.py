from mock.mock import mock


class Dispatch(object):

    @staticmethod
    def scrape_prome_kafka():
        return mock.mock_ip_list()

    @staticmethod
    def scrape_prome_ecs():
        return mock.mock_ip_list()


dispatch = Dispatch()