#coding: utf-8
from __future__ import print_function
import yaml
import uuid
from pylxd import api
import time
import ws4py.messaging
import sys, traceback
from subprocess import call
import Queue
import argparse

from utils import checkConfig

QUICKTEST=False
SEEDFILE=""
parser = argparse.ArgumentParser()
parser.add_argument("-q", "--quicktest", help="do not create nor delete container (use 'quicktest' container)",
                    action="store_true")
parser.add_argument("-f", "--file", help="seed yaml file to use")
args = parser.parse_args()
if args.quicktest:
    QUICKTEST=True
if not args.file :
    print("-f file.yml is mandatory")
    sys.exit(1)
else :
    SEEDFILE=args.file

if QUICKTEST is not True :
    CONTAINER_NAME = "temp" + str(uuid.uuid1())
else :
    CONTAINER_NAME = "quicktest"
    print ("/!\ doing operations in quicktest mode : please ensure a container named 'quicktest' already exists")

CONTAINER_TIME_WAIT_AFTER_START=10

with open(SEEDFILE, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

checkConfig(cfg)

#FIXME: there is a remote than can be configured in yml file
lxd = api.API()

try:
    configOptions = cfg.get('config', {})
    print(configOptions)
    config = {'name': CONTAINER_NAME,
              'profiles': ["default"], #TODO : profiles should be chosen according to a ~/.seed.cfg or sthing like this
              'ephemeral': False, #Can't be ephemeral since publishing needs to stop
              'source': {'type': 'image',
                        'mode': 'pull',
                        'server': cfg['source']['remote'],
                        'alias': cfg['source']['alias'],
                        },
                'config': configOptions
            }
    print(config)
    #Default build status is OK
    buildStatus=0

    if QUICKTEST is not True :
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
        print ("\n-- Command: " + command['name'])
        if command.get('exec', None) is not None :
            operation = lxd.container_run_command(CONTAINER_NAME,
                ['/bin/sh', '-c', '2>&1 ' + command['exec']],  #Redirects stderr to stdout cause can't find a way to merge websockets queues
                False,    #no interactive
                True,    # wait websocket (Needed to get metadata and sockets)
                {"HOME":command.get("home" ,"/root"),"TERM":"xterm-256color","USER":command.get("user", "root")}
            )
            operationInfo = lxd.operation_info(operation[1]['operation'])
            secrets = operation[1]['metadata']['metadata']['fds']
            wsock0 = lxd.operation_stream(operation[1]['operation'], secrets['0'])
            wsock1 = lxd.operation_stream(operation[1]['operation'], secrets['1'])
            wsock2 = lxd.operation_stream(operation[1]['operation'], secrets['2'])

            while operationInfo[1]['metadata']['status'] == "Running":
                while True:
                    try:
                        print(wsock1.messages.get(True, 0.5),end="")
                    except Queue.Empty:
                        break
                operationInfo = lxd.operation_info(operation[1]['operation'])

            if ((operationInfo[1]['metadata']['metadata']['return'] != 0) and (command.get("continue" ,False) != True)):
                buildStatus=-1
                print ("- Exiting because of previous ERROR")
                break
        elif command.get('put', None) is not None :
            #TODO: put operation implement
            print ("-- uploading file : ", command['put'] , " to ", command['todest'])
            try:
                operation = lxd.put_container_file(CONTAINER_NAME, command['put'], command['todest'])
            except:
                if(command.get("continue", False) != True):
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
        #FIXME : need contrib on pylxc
        #publish=lxd.container_publish(CONTAINER_NAME)
        CALLPARAMS=["lxc", "publish", CONTAINER_NAME, "--alias="+cfg["destination"]["alias"]]
        if (cfg['destination'].get('public', True) is True) :
            CALLPARAMS.append("--public")
        CALLPARAMS.append("description="+cfg['description'])
        for key, val  in cfg["properties"].items():
            CALLPARAMS.append(key+"="+val)

        print ("- Publishing with params :", CALLPARAMS)
        call(CALLPARAMS)
        #FIXME: publish status needs to be tested
except Exception:
    traceback.print_exc()

finally:
    #Stop in al cases
    operation = lxd.container_stop(CONTAINER_NAME, 60)
    #TODO: test if publish possible with suspend instead of stopping
    stopResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)

    #Delete in all cases
    if QUICKTEST is not True :
        print ("- Delete container " + CONTAINER_NAME)
        operation = lxd.container_destroy(CONTAINER_NAME)
        destroyResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)

print ("DONE")
