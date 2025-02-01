all: ./examples/vars ./examples/hello ./examples/funcs ./examples/labels ./examples/char ./examples/structs ./examples/structs2 ./examples/enums

./examples/%: ./examples/%.scb
	python3 scbc.py -c $<

.PHONY: clean all runall install uninstall scbclean

clean:
	rm -f ./examples/vars \
	      ./examples/hello \
	      ./examples/funcs \
	      ./examples/labels \
	      ./examples/char \
	      ./examples/structs \
	      ./examples/structs2 \
	      ./examples/enums

runall:
	echo "Running vars\n"
	./examples/vars
	echo "Running hello\n"
	./examples/hello
	echo "Running funcs\n"
	./examples/funcs
	echo "Running labels\n"
	./examples/labels
	echo "Running char\n"
	./examples/char
	echo "Running structs\n"
	./examples/structs
	echo "Running structs2\n"
	./examples/structs2
	echo "Running enums\n"
	./examples/enums

build:
	pyinstaller --onefile scbc.py

install:
	cp dist/scbc /usr/local/bin/scbc

uninstall:
	rm -f /usr/local/bin/scbc

scbclean:
	rm -rf build
	rm -rf dist
	rm -rf __pycache__
	rm -rf *.spec
	rm -rf *.pyc
	rm -rf *.pyo