import logging
from aiohttp import web
from peewee import SqliteDatabase,fn
from playhouse.shortcuts import model_to_dict

from .models import Problem

import prometheus_client as prom

logger = logging.getLogger(__name__)
vessel_gauge = prom.Gauge('problems_total', 'Total Problems Gauge', ['namespace','kind','issue','tool'])

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
    # Cleanup not current issues from vessel_gauge
    clean_q = (Problem
               .select(Problem.namespace,Problem.kind,Problem.issue,Problem.tool)
               .where(Problem.current == False))
    for clean_record in clean_q:
      vessel_gauge.labels(namespace=clean_record.namespace,kind=clean_record.kind,issue=clean_record.issue,tool=clean_record.tool).set(0)

    # Populate gauge with current records and total
    q = (Problem
        .select(Problem.namespace,Problem.kind,Problem.issue,Problem.tool,Problem.current,fn.COUNT(Problem.namespace).alias('total_problems'))
        .where(Problem.current == True)
        .group_by(Problem.namespace, Problem.kind, Problem.issue, Problem.tool)
        .order_by(Problem.namespace, Problem.kind, Problem.issue, Problem.tool))
    for record in q:
      vessel_gauge.labels(namespace=record.namespace,kind=record.kind,issue=record.issue,tool=record.tool).set(record.total_problems)

    # Return the formatted metrics output
    resp = web.Response(body=prom.generate_latest())
    resp.content_type = prom.CONTENT_TYPE_LATEST
    return resp

  async def runserver(self, port):
    try:
      await self.runner.setup()
      site = web.TCPSite(self.runner, '0.0.0.0', port)
      await site.start()
      logger.info(f"started webserver on port {port}")
    except Exception as e:
      logger.error(e)
