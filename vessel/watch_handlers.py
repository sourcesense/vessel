import threading
import _thread
from typing import List
import kopf
import logging
import asyncio

from .manager import ToolsManager
from .models import Problem

logger = logging.getLogger(__name__)

@kopf.on.event('deployments.v1.apps')
@kopf.on.event('statefulsets')
@kopf.on.event('daemonsets.v1.apps')
@kopf.on.event('jobs')
@kopf.on.event('deploymentconfigs')
def on_event(event, memo:kopf.Memo, **_):
  try:
    name = event['object']['metadata']['name']
    namespace = event['object']['metadata']['namespace']
    kind = event['object']['kind'].lower()
    logger.info(f"-> {namespace}::{kind}::{name} " + str(event['type']))

    # Cleanup previuos analysis
    query = Problem.update({Problem.current: False}).where(Problem.current == True, Problem.namespace == namespace, Problem.name == name, Problem.kind == kind)
    query.execute()
    if event['type'] != 'DELETED':
      # Create the new records
      results = memo.manager.run(event['object'], kind)
      problems = [Problem(**kw) for kw in results]
      Problem.bulk_create(problems, batch_size=100)

  except Exception as e:
    logger.error(f" on_event: {e}")
    

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
  settings.posting.level = logging.INFO

@kopf.on.cleanup()
async def cleanup_fn( **kwargs):
    logger.info("Shutting down kopf")
    

@kopf.on.login()
def login_fn(memo:kopf.Memo, **kwargs):
  if memo.token is not None:
    return kopf.ConnectionInfo(
        server=memo.url,
        token=memo.token,
        insecure=memo.insecure,
    )
  else:
    return kopf.login_with_service_account(**kwargs) or kopf.login_with_kubeconfig(**kwargs)
  

async def main_async(cancellation_event:threading.Event, memo:kopf.Memo, namespaces:List[str]):
    async def run(memo:kopf.Memo, namespaces:List[str]):
      if namespaces is not None:
        return await kopf.operator(memo=memo, namespaces=namespaces.split(','))
      else:
        return await kopf.operator(memo=memo, clusterwide=True)
    
    async def wait_for_event(e):
      loop = asyncio.get_event_loop()
      await loop.run_in_executor(None, e.wait)
    
    done, pending = await asyncio.wait(
          [wait_for_event(cancellation_event),  run(memo, namespaces)],
          return_when=asyncio.FIRST_COMPLETED
      )
    if cancellation_event.is_set():  
      for t in pending:
        logger.debug(f"Cancelling {t}...")
        t.cancel()
    else:
      if next(iter(done)).exception():
        _thread.interrupt_main() 
        
def kopf_thread(event:threading.Event, manager:ToolsManager, namespaces:List[str], url:str, token:str, insecure:bool):
  memo = kopf.Memo()
  memo.manager = manager
  memo.url = url
  memo.token = token
  memo.insecure = insecure
  asyncio.run(main_async(event, memo, namespaces))
