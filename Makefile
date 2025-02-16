all: ./examples/vars ./examples/hello ./examples/funcs ./examples/labels ./examples/char ./examples/structs ./examples/structs2 ./examples/enums ./examples/stringbuff ./examples/pointer ./examples/pointer2 ./examples/arrays ./examples/shifts ./examples/get_value

./examples/%: ./examples/%.scb
	python3 scbc.py -c $<
	python3 scbc.py $<

.PHONY: clean all runall install uninstall scbclean

clean:
	rm -f ./examples/vars \
	      ./examples/hello \
	      ./examples/funcs \
	      ./examples/labels \
	      ./examples/char \
	      ./examples/structs \
	      ./examples/structs2 \
	      ./examples/enums \
	      ./examples/stringbuff \
	      ./examples/pointer \
	      ./examples/pointer2 \
	      ./examples/arrays \
	      ./examples/shifts \
	      ./examples/get_value \
	      ./examples/*.s

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
	echo "Running stringbuff\n"
	./examples/stringbuff
	echo "Running pointer\n"
	./examples/pointer
	echo "Running pointer2\n"
	./examples/pointer2
	echo "Running arrays\n"
	./examples/arrays
	echo "Running shifts\n"
	./examples/shifts
	echo "Running get_value\n"
	./examples/get_value

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