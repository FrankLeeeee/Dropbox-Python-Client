import click

from .utils import credential, download, upload


class Arguments():

    def __init__(self, arg_dict):
        for k, v in arg_dict.items():
            self.__dict__[k] = v


@click.group()
def cli():
    pass


cli.add_command(credential)
cli.add_command(upload)
cli.add_command(download)

if __name__ == '__main__':
    cli()
