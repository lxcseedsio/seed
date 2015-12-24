#coding: utf-8

import yaml
import uuid
from pylxd import api
import time
import ws4py.messaging

CONTAINER_NAME = "temp"
#CONTAINER_NAME += str(uuid.uuid1())
CONTAINER_TIME_WAIT_AFTER_START=0


with open("seed.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

lxd = api.API()

try:
    lxd.container_defined(CONTAINER_NAME)
except Exception as e:
    print("Container does exist: %s" % e)

config = {'name': CONTAINER_NAME,
          'profiles': ["default"],
          'ephemeral': False, #Can't be ephemeral since publishing needs to stop
          'source': {'type': 'image',
                    'mode': 'pull',
                    'server': cfg['source']['remote'],
                    'alias': cfg['source']['alias'],
                    }
        }
print "Creating"
operation = lxd.container_init(config)
creationResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)
#TODO exit if non 200

#Start
print "Starting"
operation = lxd.container_start(CONTAINER_NAME, 60)
startResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)
#TODO exit if non 200

#Sleep some seconds to ensure container start is really done
print "Waiting"
time.sleep(CONTAINER_TIME_WAIT_AFTER_START)

#Do exec
print "Excuting"
operation = lxd.container_run_command(CONTAINER_NAME,
    ['/bin/sh', '-c', cfg['exec']],
    False,    # interactive
    True,    # wait websocket
    {"HOME":"/root","TERM":"xterm-256color","USER":"root"}
)


print "Run Ope : "
secrets = operation[1]['metadata']['metadata']['fds']
print secrets

wsock0 = lxd.operation_stream(operation[1]['operation'], secrets['0'])
wsock1 = lxd.operation_stream(operation[1]['operation'], secrets['1'])
wsock2 = lxd.operation_stream(operation[1]['operation'], secrets['2'])
#result = wsock.receive()
#wsock.close()
#result2 = wsock2.receive()
#for message in iter(wsock0.messages, None):
#print wsock0.messages.get()
#for message in iter(wsock1.messages, None):
#while not wsock1.messages.empty():

#print wsock1.messages
#print wsock2.messages

runResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)
print "Run result"

#print wsock1.messages.task_done()
stdout = wsock1.messages.get()
#FIXME : this is no good way to itearate over queues
if (isinstance(stdout, ws4py.messaging.BinaryMessage)):
    print stdout

stderr = wsock2.messages.get()
#FIXME : same here
if (isinstance(stderr, ws4py.messaging.BinaryMessage)):
    print stderr

#TODO exit if non 200

#TODO get result through web socket

#TODO publish

#TODO remove

print "DONE"
