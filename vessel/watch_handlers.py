
from typing import List
import kopf
import click
import logging
import asyncio

from .manager import ToolsManager
from .models import Problem

@kopf.on.event('deployments.v1.apps')
@kopf.on.event('statefulsets')
@kopf.on.event('daemonsets.v1.apps')
@kopf.on.event('jobs')
@kopf.on.event('deploymentconfigs')
def on_event(event, memo:kopf.Memo, **_):
  try:
    name = event['object']['metadata']['name']
    namespace = event['object']['metadata']['namespace']
    kind = event['object']['kind']
    click.echo(f"-> {namespace}::{kind}::{name}")
    if event['type'] =='DELETED':
      print('handle deletion')
      query = Problem.update({Problem.current: False}).where(Problem.current == True, Problem.namespace == namespace, Problem.name == name, Problem.kind == kind)
      query.execute()  
    else:  
      results = memo.manager.run(event['object'], kind)
      # cleanup previos analysis
      query = Problem.update({Problem.current: False}).where(Problem.current == True, Problem.namespace == namespace, Problem.name == name, Problem.kind == kind)
      query.execute()  
      problems = [Problem(**kw) for kw in results]
      
      Problem.bulk_create(problems, batch_size=100)

  except Exception as e:
    click.echo(e, err=True)
    

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
  click.echo("kopf started")
  settings.posting.level = logging.DEBUG

@kopf.on.login()
def login_fn(memo:kopf.Memo, **kwargs):
  if memo.token is not None:
    return kopf.ConnectionInfo(
        server=memo.url,
        token=memo.token,
    )
  else:
    return kopf.login_with_service_account(**kwargs) or kopf.login_with_kubeconfig(**kwargs)

def kopf_thread(manager:ToolsManager, namespaces:List[str], url:str, token:str):
  memo = kopf.Memo()
  memo.manager = manager
  memo.url = url
  memo.token = token
  if namespaces is not None:
    asyncio.run(kopf.operator(memo=memo, namespaces=namespaces.split(',')))
  else:
    asyncio.run(kopf.operator(memo=memo, clusterwide=True))
