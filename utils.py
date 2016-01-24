import sys

def checkConfig(cfg):
    print ("- Checking config file")

    if (cfg.get('source', None) == None):
        print ("-- Source is mandatory with attributes remote and alias")
        sys.exit(1)
    if (cfg['source'].get('remote', None) == None):
        print ("-- Remote source lxd is mandatory")
        sys.exit(1)
    if (cfg['source'].get('alias', None) == None):
        print ("-- Alias source is mandatory")
        sys.exit(1)

    if (cfg.get('destination', None) == None):
        print ("-- Destination is mandatory with attributes remote and alias")
        sys.exit(1)
    if (cfg['destination'].get('alias', None) == None):
        print ("-- Destination alias is mandatory")
        sys.exit(1)
    if (cfg['destination'].get('remote', None) != "local"):
        print ("-- Please note : remote is not supported")
