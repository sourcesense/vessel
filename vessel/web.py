import logging
from aiohttp import web
from peewee import SqliteDatabase,fn
from playhouse.shortcuts import model_to_dict

from .models import Problem

import prometheus_client as prom

logger = logging.getLogger(__name__)
# Available fields:
# - name
# - namespace
# - kind
# - issue
# - issue_metadata
# - tool
vessel_total_issues = prom.Gauge('total_issues', 'Total issues')
vessel_total_ns_issues = prom.Gauge('total_ns_issues', 'Total issues per namespace', ['namespace'])
vessel_total_kind_issues = prom.Gauge('total_kind_issues', 'Total issues per kind', ['kind'])
vessel_total_issue_issues = prom.Gauge('total_issue_issues', 'Total issues per issue', ['issue'])

class WebServer(object):
  def __init__(self, db:SqliteDatabase):
    super().__init__()
    self.db = db
    self.app = web.Application()
    self.app.router.add_get('/', self.index)
    self.app.router.add_get('/query', self.query)
    self.app.router.add_get('/metrics', self.metrics)
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
    
    q = Problem.select().where(*query_params)
    result = [model_to_dict(m) for m in list(q.paginate(int(page), int(size)))]
    
    return web.json_response({
      "size": int(size),
      "count": q.count(),
      "page": int(page),
      "result": result,
    })

  async def metrics(self, request):
    # Populate gauge with total issues
    q = (Problem
        .select(fn.COUNT().alias('total_issues'))
        .where(Problem.current == True))
    vessel_total_issues.set(q[0].total_issues)

    # Update other totals
    self.prom_update_total('namespace', vessel_total_ns_issues, 'total_ns_issues')
    self.prom_update_total('kind', vessel_total_kind_issues, 'total_kind_issues')
    self.prom_update_total('issue', vessel_total_issue_issues, 'total_issue_issues')

    # Return the formatted metrics output
    resp = web.Response(body=prom.generate_latest())
    resp.content_type = prom.CONTENT_TYPE_LATEST
    return resp

  async def prom_update_total(self, resource_name, prom_resource, total_name):
    # Cleanup not current issues
    clean_q = (Problem
               .select(getattr(Problem, resource_name))
               .where(Problem.current == False))
    for clean_record in clean_q:
      prom_resource.labels(**{resource_name: getattr(clean_record, resource_name)}).set(0)

    # Populate gauge with current records and total
    q = (Problem
        .select(getattr(Problem, resource_name),fn.COUNT(getattr(Problem, resource_name)).alias(total_name))
        .where(Problem.current == True)
        .group_by(getattr(Problem, resource_name))
        .order_by(getattr(Problem, resource_name)))
    for record in q:
      #import pdb; pdb.set_trace()
      prom_resource.labels(**{resource_name: getattr(record, resource_name)}).set(getattr(record, total_name))

  async def runserver(self, port):
    try:
      await self.runner.setup()
      site = web.TCPSite(self.runner, '0.0.0.0', port)
      await site.start()
      logger.info(f"started webserver on port {port}")
    except Exception as e:
      logger.error(e)
