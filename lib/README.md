# CPS libraries
## Summary
- `cps` - common functions used by other libraries
- `accel` - MPU-6050 accelerometer library
- `dlx` - Dynamixel XM430-W350-R servo library

## Examples
Folder `examples` contains example programs for different libraries.

To compile an example:
```bash
# navigate to lib/ (where this README file is)
mkdir build
cd build/
cmake ..
make <lib-name>-example
./<lib-name>-example
```

So for `accel` library:
```bash
make accel-example
./accel-example
```