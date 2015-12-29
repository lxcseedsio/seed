
#TODO: move this func to a different file
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

    if (cfg.get('properties', None) == None):
        print ("-- Properties is mandatory with at least attributes tag and type")
        sys.exit(1)
    if (cfg['properties'].get('tag', None) == None):
        print ("-- Tag property is mandatory")
        sys.exit(1)
    #FIXME: this test is not failing if value is different from expected
    if (cfg['properties'].get('type', None) == None):
        print ("-- Type property is mandatory and must be one of : micro, fat, infra, devstack or other")
        sys.exit(1)
