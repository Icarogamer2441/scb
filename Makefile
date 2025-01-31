all: ./examples/vars ./examples/hello ./examples/funcs ./examples/labels ./examples/char ./examples/structs ./examples/structs2

./examples/%: ./examples/%.scb
	python3 scbc.py -c $<

.PHONY: clean all runall

clean:
	rm -f ./examples/vars \
	      ./examples/hello \
	      ./examples/funcs \
	      ./examples/labels \
	      ./examples/char \
	      ./examples/structs \
	      ./examples/structs2

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