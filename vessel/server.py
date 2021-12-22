import asyncio
import signal
import threading
import logging
import sys
from typing import List
from peewee import SqliteDatabase

from vessel.manager import ToolsManager
from .models import Problem
from .web import WebServer
from .watch_handlers import kopf_thread

logger = logging.getLogger(__name__)

def handle_sighup():
  sys.exit(0)

async def graceful_shutdown(db, ioloop, cancellation_event:asyncio.Event):
  logger.info("Graceful Shutdown...")
  db.close()
  cancellation_event.set()
  ioloop.stop()
  sys.exit(0)

def start(data:str, manager:ToolsManager, namespaces:List[str], k8s_url:str, k8s_token:str):
  ioloop = asyncio.get_event_loop()
  ioloop.add_signal_handler(signal.SIGHUP, handle_sighup)
  ioloop.add_signal_handler(signal.SIGINT, handle_sighup)
  ioloop.add_signal_handler(signal.SIGTERM, handle_sighup)

  #db configuration 
  db = SqliteDatabase(data)
  Problem.bind(db)
  
  db.connect()
  db.create_tables([Problem])

  webserver = WebServer(db, )
  ioloop.create_task(webserver.runserver(8089))
  # https://pymotw.com/3/asyncio/executors.html

  cancellation_event = threading.Event()
  try:
    thread = threading.Thread(target=kopf_thread, 
      args=(cancellation_event, manager, namespaces, k8s_url, k8s_token), daemon=True)
    thread.start()
    ioloop.run_forever()
    thread.join()
    
  except SystemExit:
    asyncio.run(graceful_shutdown(db, ioloop, cancellation_event))
  

