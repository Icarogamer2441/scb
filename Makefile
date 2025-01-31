all: ./examples/vars ./examples/hello ./examples/funcs ./examples/labels ./examples/char

./examples/%: ./examples/%.scb
	python3 scbc.py -c $<

.PHONY: clean all

clean:
	rm -f ./examples/vars
	rm -f ./examples/hello
	rm -f ./examples/funcs
	rm -f ./examples/labels
	rm -f ./examples/char
	rm -f ./examples/array