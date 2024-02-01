.PHONY: build-mi_cps install-mi_cps

BUILD-DIR = build

build-mi_cps:
	cmake -S . -B "$(BUILD-DIR)"
	make -C "$(BUILD-DIR)" mi_cps
	mkdir -p "$(BUILD-DIR)/include/mi_cps"
	cp accel/accel.h cps/cps.h dist/dist.h dxl/dxl.h "$(BUILD-DIR)/include/mi_cps"

install-mi_cps:
	cp "$(BUILD-DIR)/libmi_cps.so" /usr/local/lib/libmi_cps.so
	rm -rf /usr/local/include/mi_cps
	cp -r "$(BUILD-DIR)/include/mi_cps" /usr/local/include/mi_cps

clean:
	rm -rf "$(BUILD-DIR)"
