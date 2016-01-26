# seed

Tool for creating lxc images using lxd servers. The script use pure REST Api on lxd daemons.

## Installation

pip install -r requirements.txt

## Usage

```
usage: seed.py [-h] [-f FILE] [-t TIMEOUT_ON_START] [-n NAME] [--no-delete]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  seed yaml file to use
  -t TIMEOUT_ON_START, --timeout-on-start TIMEOUT_ON_START
                        timeout while waiting container to start in seconds
                        (default 10)
  -n NAME, --name NAME  name of the container to be used
  --no-delete           do not delete at the end of process
```

## Example

Creating an image based on yaml file :
``python seed.py -f test.yml``

Creating using a named container and no destroying it (usefull for troubleshooting) :
``python seed.py -f test.yml -n testcontainer --no-delete``


## Yaml file structure

Yaml file can handle is structured this way.

### Headers

``description`` : mandatory description of the lxc image to be pushed

``config`` : optional config options to be used when creating container used to build image

``source`` : remote lxd server and  image alias used to create container

``remote`` : remote lxd server and image alias to be published

``properties`` : optional properties that will be sent when publishing

### Commands

Commands go in ``commands`` section. All commands begin with ``name``.

- Exec commands are used to exec  commands on container :

```
- name: exec rm #Mandatory name
  exec: rm -f /tmp/test #Mandatory exec comand
  user: root #Optional user to be used when executing
  home: /root #Optional home dir to be used
```

- Put file commands are used to send a file :

```
- name: put file #Mandatory name
  put: ./testput.file #File to be pushed
  todest: /tmp/putted.file #Where the filed should be pushed
```

All commands also specify ``continue: true`` to tell script should not stop even if command failed :
```
- name: put file
  exec: failingCommand.sh
  continue: true
```

## Examples
You can take a look at real working examples in test.yml file or at official public lxcseeds.io : https://github.com/lxcseedsio/images

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request

## History
0.1 :
- fully functional script

first devs :
- no more needing lxc local command file
- added config options when creating container
- added operation to put file
- really beta: can build, can publish

## Credits

Credits lxcsseds.io

## License

MIT
