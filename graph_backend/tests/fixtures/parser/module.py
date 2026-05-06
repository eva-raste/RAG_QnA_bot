import os
from pkg import helper


class Service:
    def run(self):
        helper()


def build():
    Service().run()
