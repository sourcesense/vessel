from typing import List
import pluggy
import pkgutil
import click
import importlib
import inspect
import logging
from . import tools as tools_impl
from .models import Issue, Context

vessel_spec = pluggy.HookspecMarker("vessel")
vessel_hook = pluggy.HookimplMarker("vessel")
logger = logging.getLogger(__name__)
class ToolSpec:
  """Spec for tools"""
  @vessel_spec
  def deployment(self, resource, ctx): # pylint:disable=
    pass
  @vessel_spec
  def deploymentconfig(self, resource, ctx):
    pass
  @vessel_spec
  def job(self, resource, ctx):
    pass
  @vessel_spec
  def statefulset(self, resource, ctx):
    pass
  @vessel_spec
  def daemonset(self, resource, ctx):
    pass

def vessel_result(res:List[Issue]):
  frm = inspect.stack()[1]
  mod = inspect.getmodule(frm[0])
  final = []
  for r in res:
    if not isinstance(r, Issue):
      raise click.ClickException('tool output is not correct')
    final.append({
      "issue": r.name,
      "issue_metadata": r.metadata,
      "tool": mod.__name__
    })  
    
  return final

class ToolsManager():
  def __init__(self, tasks:List[str], context:Context) -> None:
    self.pm = pluggy.PluginManager("vessel")
    self.pm.add_hookspecs(ToolSpec)
    self.ctx = context
    
    # register plugins
    for _, modname, _ in pkgutil.walk_packages(path=tools_impl.__path__):
      if modname in tasks:
        mod = importlib.import_module(f'{tools_impl.__name__}.{modname}')
        self.pm.register(mod)
        
  def run(self, resource:dict, kind:str) -> List[dict]:
    name = resource['metadata']['name']
    namespace = resource['metadata']['namespace']
    try:
      hook_to_run = getattr(self.pm.hook, kind.lower())
    except AttributeError as err:
      logger.error(f"No tool registered to handle [{kind}]:  resource {err}")
      return None
    issues = hook_to_run(resource=resource, ctx=self.ctx)
    return [dict({"name": name, "namespace": namespace, "kind": kind}, **i) for sublist in issues for i in sublist ]
    
    
    
  