.PHONY: build-so install-so

BUILD-DIR = build

build-so:
	cmake -S . -B "$(BUILD-DIR)"
	make -C "$(BUILD-DIR)" mi_cps
	mkdir -p "$(BUILD-DIR)/include/mi_cps"
	cp accel/accel.h cps/cps.h dist/dist.h dxl/dxl.h "$(BUILD-DIR)/include/mi_cps"

install-so:
	cp "$(BUILD-DIR)/libmi_cps.so" /usr/local/lib/libmi_cps.so
	rm -rf /usr/local/include/mi_cps
	cp -r "$(BUILD-DIR)/include/mi_cps" /usr/local/include/mi_cps

build-py:
	cd python_api && python3 setup.py build

install-py:
	cd python_api && python3 setup.py install

clean:
	rm -rf "$(BUILD-DIR)"
