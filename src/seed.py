#coding: utf-8

import yaml
import uuid
from pylxd import api
import time

with open("seed.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Let's pick a random name, avoiding clashes
CONTAINER_NAME = "temp"
CONTAINER_NAME += str(uuid.uuid1())

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
time.sleep(30)

#Do exec
print "Excuting"
operation = lxd.container_run_command(CONTAINER_NAME,
    ['/bin/sh', '-c', cfg['exec']],
    False,    # interactive
    False,    # wait websocket
    {"HOME":"/root","TERM":"xterm-256color","USER":"root"}
)
runResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)
#TODO exit if non 200

#TODO get result through web socket

#TODO publish

#TODO remove

print "DONE"
