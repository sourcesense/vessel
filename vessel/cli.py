import click
import yaml
import json
from .manager import ToolsManager

@click.group()
def cli():
    pass

@cli.command()
@click.argument('resource', type=click.File())
@click.option('-t', '--tools', envvar='TASKS', default="linter", type=click.STRING, help="Tools to run separated by commas [default]")
def single(resource, tools):
    """Runs vessel one shot against a resource."""
    res:dict = yaml.safe_load(resource)
    manager = ToolsManager(tools)
    results = manager.run(res)
    ret = []
    for res in results:
        ret.extend(res)

    click.echo( json.dumps(ret, indent=2) )


@cli.command()
@click.option('-n', '--namespaces', envvar='NAMESPACES', default="default", type=click.STRING, help="Namespaces to watch separated by commas [default]")
@click.option('-t', '--tools', envvar='TASKS', default="linter", type=click.STRING, help="Tools to run separated by commas [default]")
@click.option('-d', '--data', envvar='DATA', type=click.Path(exists=True, dir_okay=False, writable=True), help="data file [./data.db]")
@click.option('--k8s-url', envvar='K8S_URL', type=click.STRING, help="Kubernetes url, if null service account will be used [null]")
@click.option('--k8s-token', envvar='K8S_TOKEN', type=click.STRING, help="Kubernetes authentication token [null]")
def server(namespaces, tools, data, k8s_url, k8s_token):
    """Run vessel as server in watch mode."""
    click.echo( namespaces)



    