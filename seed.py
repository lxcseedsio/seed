#coding: utf-8
from __future__ import print_function
import yaml
import uuid
from pylxd import api
import time
import sys, traceback
from subprocess import call
import Queue
import argparse

from utils import checkConfig

SEEDFILE=""
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="seed yaml file to use")
parser.add_argument("-t", "--timeout-on-start", help="timeout while waiting container to start in seconds (default 10)")
parser.add_argument("-n", "--name", help="name of the container to be used")
parser.add_argument("--no-delete", help="do not delete at the end of process", action="store_true")
args = parser.parse_args()

print(args)
if not args.timeout_on_start :
    CONTAINER_TIME_WAIT_AFTER_START = 10
else :
    CONTAINER_TIME_WAIT_AFTER_START = float(args.timeout_on_start)

if not args.file :
    print("-f file.yml is mandatory")
    sys.exit(1)
else :
    SEEDFILE=args.file

if args.name is not None :
    CONTAINER_NAME = args.name
else :
    CONTAINER_NAME = "temp" + str(uuid.uuid1())

with open(SEEDFILE, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

checkConfig(cfg)

#FIXME: there is a remote than can be configured in yml file
lxd = api.API()

try:
    configOptions = cfg.get('config', {})
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
    print ("- Waiting " + str(CONTAINER_TIME_WAIT_AFTER_START) + "s for container init process")
    time.sleep(CONTAINER_TIME_WAIT_AFTER_START) #FIXME : should test (with timeout) if container and at least one eth is UP

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
    stopResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)

    #Publish (only if build successfull)
    if (buildStatus == 0):
        publishDict= {
            "public": cfg['destination'].get('public', True),         # true or false
            "filename": "/tmp/" + CONTAINER_NAME,     # Used for export
            "source": {
                "type": "container",  # One of "container" or "snapshot"
                "name": CONTAINER_NAME
            },
            "properties": {           # Image properties
            },
        }

        if cfg.get("properties", None) != None :
            for key, val  in cfg["properties"].items():
                publishDict["properties"][key]=val

        publishDict["properties"]["description"]=cfg['description']

        print ("- Publishing with params : ", publishDict)

        operation=lxd.container_publish(publishDict)
        publishResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)

        fingerprint = lxd.operation_info(operation[1]['operation'])[1]['metadata']['metadata']['fingerprint']
        aliasDict = {
            'description': cfg['description'],
            'target': fingerprint,
            'name': cfg['destination']['alias']
        }

        #Check if alias exists
        oldImage = None
        try:
            oldImage = lxd.alias_show(cfg["destination"]["alias"])
            aliasList = lxd.alias_list()
            print("- Alias was defined with image : ", oldImage)
        except:
            print("- Alias was never defined")
        if oldImage is not None :
            print("- Deleting old alias")
            lxd.alias_delete(cfg["destination"]["alias"])
            print ("- Creating new alias ", cfg["destination"]["alias"])
            lxd.alias_create(aliasDict)
            print("- Deleting old image associated with alias")
            lxd.image_delete(oldImage[1]['metadata']['target'])
        else :
            print ("- Creating alias : ", cfg["destination"]["alias"])
            lxd.alias_create(aliasDict)

except Exception:
    traceback.print_exc()

finally:
    #Stop in all cases
    operation = lxd.container_stop(CONTAINER_NAME, 60)
    stopResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)

    #Delete in all cases
    if args.no_delete is not True :
        print ("- Delete container " + CONTAINER_NAME)
        operation = lxd.container_destroy(CONTAINER_NAME)
        destroyResult = lxd.wait_container_operation(operation[1]['operation'],200, 60)

print ("DONE")
