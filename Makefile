CC = cc
PYTHON = python3
CORE_FLAGS = -std=c11 -Wall -Wextra -Werror -Wconversion -pedantic -Icore
UPSTREAM = vendor/ThisFirmwareDoesNotExist
UV = UV_CACHE_DIR=$(CURDIR)/.cache/uv uv

.PHONY: test test-c test-python test-sanitize stock-test native-test demo check-arm setup upstream-test lint

test: test-c test-python

build:
	mkdir -p build

build/test_freaklocks: core/freaklocks.c core/freaklocks.h tests/test_freaklocks.c | build
	$(CC) $(CORE_FLAGS) -O2 core/freaklocks.c tests/test_freaklocks.c -o $@

test-c: build/test_freaklocks
	./build/test_freaklocks

test-python:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

test-sanitize: | build
	$(CC) $(CORE_FLAGS) -O1 -g -fsanitize=address,undefined core/freaklocks.c tests/test_freaklocks.c -o build/test_freaklocks_sanitize
	./build/test_freaklocks_sanitize

build/freaklocks_demo: core/freaklocks.c core/freaklocks.h examples/freaklocks_demo.c | build
	$(CC) $(CORE_FLAGS) -O2 core/freaklocks.c examples/freaklocks_demo.c -o $@

demo: build/freaklocks_demo
	./build/freaklocks_demo

check-arm: | build
	clang $(CORE_FLAGS) --target=thumbv7em-none-eabi -mcpu=cortex-m4 -mthumb -Os -ffreestanding -c core/freaklocks.c -o build/freaklocks-arm.o

build/libfreaklocks.so: core/freaklocks.c core/freaklocks.h | build
	$(CC) $(CORE_FLAGS) -O2 -shared -fPIC core/freaklocks.c -o $@

stock-test: build/libfreaklocks.so
	$(UV) run --project $(UPSTREAM) --frozen python -m unittest discover -s tests -p 'test_stock_sequencer.py' -v

native-test:
	$(UV) run --project $(UPSTREAM) --frozen python -m unittest discover -s tests -p 'test_native*.py' -v

setup:
	$(UV) sync --project $(UPSTREAM) --frozen

upstream-test:
	$(UV) run --project $(UPSTREAM) --frozen python -m pytest $(UPSTREAM)/tests -ra

lint:
	$(UV) run --project $(UPSTREAM) --frozen ruff check tools tests
	$(UV) run --project $(UPSTREAM) --frozen ruff format --check tools tests
