from aiohttp import web
from peewee import SqliteDatabase
import click
from playhouse.shortcuts import model_to_dict
from .models import Problem

class WebServer(object):
  def __init__(self, db:SqliteDatabase):
    super().__init__()
    self.db = db
    self.app = web.Application()
    self.app.router.add_get('/', self.index)
    self.app.router.add_get('/query', self.query)
    self.runner = web.AppRunner(self.app)
    self.routes = web.RouteTableDef()
    

  async def index(self, _):
    return web.json_response({
      "name": "Vessel Collector",
    })

  async def query(self, request):
    size = request.query.get('size', 20)
    page = request.query.get('page', 1)
    
    query_params = [ getattr(Problem, key).in_(request.query.getall(key)) for key in request.query.keys() if key in Problem.__dict__ ]
    query_params.append(Problem.current == True)
    
      
    result = [model_to_dict(m) for m in list(Problem.select().where(*query_params).paginate(int(page), int(size)))]
    
    return web.json_response({
      "size": int(size),
      "count": len(result),
      "page": int(page),
      "result": result,
    })

  async def runserver(self, port):
    try:
      await self.runner.setup()
      site = web.TCPSite(self.runner, '0.0.0.0', port)
      await site.start()
      click.echo(f"started webserver on port {port}")
    except Exception as e:
      click.echo(e)



