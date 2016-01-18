# seed

Tool for creating lxc images using lxd servers

## Installation

pip install -r requirements.txt

## Usage

python seed.py -f file.yml

Options:
-q : do things with quicktest mode (need a previously container named quicktest)
-t time : wait time in seconds after lxc container is started before doing commands

## Config structure

See test.yml for more details

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request

## History
no more needing lxc local command file
added config options when creating container
added operation to put file
really beta: can build, can publish

## Credits

Credits lxcsseds.io

## License

MIT
