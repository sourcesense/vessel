from typing import List
import pluggy
import pkgutil
import click
import importlib
from . import tools as tools_impl
 
vessel_spec = pluggy.HookspecMarker("vessel")
vessel_hook = pluggy.HookimplMarker("vessel")

class ToolSpec:
  """Spec for tools"""
  @vessel_spec
  def deployment(self, resource): # pylint:disable=
    pass
  @vessel_spec
  def deploymentconfig(self, arg1, arg2):
    pass
  @vessel_spec
  def job(self, arg1, arg2):
    pass
    

class ToolsManager():
  def __init__(self, tasks:List[str]) -> None:
    self.pm = pluggy.PluginManager("vessel")
    self.pm.add_hookspecs(ToolSpec)
    
    # register plugins
    for _, modname, _ in pkgutil.walk_packages(path=tools_impl.__path__):
      if modname in tasks:
        mod = importlib.import_module(f'{tools_impl.__name__}.{modname}')
        self.pm.register(mod)
    
  def run(self, resource:dict) -> List[dict]:
    kind = resource['kind']
    try:
      hook_to_run = getattr(self.pm.hook, kind.lower())
    except AttributeError as err:
      click.echo(f"No tool registered to handle [{kind}]:  resource {err}")
      return None
    return hook_to_run(resource=resource)
    
    
    
  