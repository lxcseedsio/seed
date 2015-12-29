#coding: utf-8
from __future__ import print_function
import yaml
import uuid
from pylxd import api
import time
import ws4py.messaging
import sys
from utils import checkConfig

CONTAINER_NAME = "temp" + str(uuid.uuid1())
CONTAINER_TIME_WAIT_AFTER_START=10

with open("seed.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

checkConfig(cfg)

lxd = api.API()

#FIXME using uuid container test should not be necessary
try:
    lxd.container_defined(CONTAINER_NAME)
except Exception as e:
    print("Container does exist: %s" % e)

config = {'name': CONTAINER_NAME,
          'profiles': ["default"], #TODO : profiles should be chosen according to a ~/.seed.cfg or sthing like this
          'ephemeral': False, #Can't be ephemeral since publishing needs to stop
          'source': {'type': 'image',
                    'mode': 'pull',
                    'server': cfg['source']['remote'],
                    'alias': cfg['source']['alias'],
                    }
        }

#Default build status is OK
buildStatus=0

print ("- Creating container with name " + CONTAINER_NAME)
operation = lxd.container_init(config)
creationResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)
#TODO exit if non 200

#   Start
print ("- Starting container " + CONTAINER_NAME)
operation = lxd.container_start(CONTAINER_NAME, 60)
startResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)
#TODO exit if non 200

#Sleep some seconds to ensure container start is really done
print ("- Waiting a little for container init process")
time.sleep(CONTAINER_TIME_WAIT_AFTER_START) #TODO : should be configurable but with a max test

#Do exec
print ("- executing commands")
for command in cfg['commands']:
    print ("-- Command: " + command['name'])
    operation = lxd.container_run_command(CONTAINER_NAME,
        ['/bin/sh', '-c', command['exec']],
        False,    #no interactive
        True,    # wait websocket
        {"HOME":command.get("home" ,"/root"),"TERM":"xterm-256color","USER":command.get("user", "root")}
    )

    secrets = operation[1]['metadata']['metadata']['fds']
    wsock0 = lxd.operation_stream(operation[1]['operation'], secrets['0'])
    wsock1 = lxd.operation_stream(operation[1]['operation'], secrets['1'])
    wsock2 = lxd.operation_stream(operation[1]['operation'], secrets['2'])

    runResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)
    operationResult = lxd.operation_info(operation[1]['operation'])

    stdout = wsock1.messages.get()
    #FIXME : this is no good way to itearate over queues
    if (isinstance(stdout, ws4py.messaging.BinaryMessage)):
        print (stdout)

    stderr = wsock2.messages.get()

    #FIXME : same ugly test here
    if (isinstance(stderr, ws4py.messaging.BinaryMessage)):
        print(stderr, file=sys.stderr)

    if ((operationResult[1]['metadata']['metadata']['return'] != 0) and (command.get("continue" ,False) != True)):
        buildStatus=-1
        print ("- Exiting because of previous ERROR")
        break

#Stop in any case
print ("- Stopping container " + CONTAINER_NAME)
operation = lxd.container_stop(CONTAINER_NAME, 60)
#TODO: test if publish possible with suspend instead of stopping
stopResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)

#Publish (only if build successfull)
if (buildStatus == 0):
    #FIXME : does not work -> patch needed for py lxd
    publish=lxd.container_publish(CONTAINER_NAME)
    #Fallback to sys call
    #lxc publish --public --alias=

#Delete in all cases
print ("- Delete container " + CONTAINER_NAME)
operation = lxd.container_destroy(CONTAINER_NAME)
destroyResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)

print ("DONE")
