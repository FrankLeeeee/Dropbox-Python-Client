import os
import os.path as osp

import click

from dbx.client import DropboxClient


class CacheDirectory:

    def __init__(self):
        self.home_dir = osp.expanduser('~')
        self.cache_dir = osp.join(self.home_dir, '.cache', 'dbx')

    def make_dirs(self):
        if not osp.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def write_token(self, token):
        credential_file = osp.join(self.cache_dir, 'keys')
        with open(credential_file, 'w') as f:
            f.write(token)

    def read_toekn(self):
        credential_file = osp.join(self.cache_dir, 'keys')
        with open(credential_file, 'r') as f:
            token = f.read()
        return token


@click.command()
@click.option('-s', '--src', required=True, help='File path to upload')
@click.option('-d', '--dst', required=True, help='Dropbox upload path')
def upload(src, dst):
    token = CacheDirectory().read_toekn()
    client = DropboxClient(token)
    client.connect()
    client.upload(src, dst)


@click.command()
@click.option('-s', '--src', required=True, help='Dropbox download path')
@click.option('-d', '--dst', required=True, help='Local file path as destination')
def download(src, dst):
    token = CacheDirectory().read_toekn()
    client = DropboxClient(token)
    client.connect()
    client.download(src, dst)


@click.command()
@click.option('--token', required=True, help='Dropbox token')
def credential(token):
    # save credentials in ~/.cache/dbx/keys
    cache_dir = CacheDirectory()
    cache_dir.make_dirs()
    cache_dir.write_token(token)
