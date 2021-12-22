import click
import yaml
import json
import logging
from .models import Context
from .manager import ToolsManager
from .server import start


@click.group()
def cli():
    pass

@cli.command()
@click.argument('resource', type=click.File())
@click.option('-t', '--tools', envvar='TASKS', default="linter", type=click.STRING, help="Tools to run separated by commas [default]")
@click.option('--registries', default=None, envvar='REGISTRIES', type=click.File( 'rb'), help="json file with registries mapping credentials [None]")
def single(resource, tools, registries):
    """Runs vessel one shot against a resource."""
    res:dict = yaml.safe_load(resource)

    ctx = Context(registries)
    manager = ToolsManager(tools, ctx)
    results = manager.run(res, res['kind'])
    # todo:  analyze result and exit with non zero value
    click.echo( json.dumps(results, indent=2) )


@cli.command()
@click.option('-n', '--namespaces', envvar='NAMESPACES', default=None, type=click.STRING, help="Namespaces to watch separated by commas [default]")
@click.option('-t', '--tools', envvar='TOOLS', default="linter,trivy", type=click.STRING, help="Tools to run separated by commas [default]")
@click.option('-d', '--data', default='./data.db', envvar='DATA', type=click.Path( dir_okay=False, writable=True), help="data file [./data.db]")
@click.option('--k8s-url', envvar='K8S_URL', type=click.STRING, help="Kubernetes url, if null service account will be used [null]")
@click.option('--k8s-token', envvar='K8S_TOKEN', type=click.STRING, help="Kubernetes authentication token [null]")
@click.option('--registries', default=None, envvar='REGISTRIES', type=click.File( 'rb'), help="json file with registries mapping credentials [None]")
@click.option('--verbose',is_flag=True, default=False)
def server(namespaces, tools, data, k8s_url, k8s_token, registries, verbose):
    """Run vessel as server in watch mode."""
    click.echo(f"Running for namespaces: {namespaces}")
    ctx = Context(registries)
    manager = ToolsManager(tools, ctx)
    logging.basicConfig(format='%(asctime)s [%(module).8s][%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S', level=logging.DEBUG if verbose else logging.INFO)

    logging.info("Starting Vessel")
    start(data, manager, namespaces, k8s_url, k8s_token)



