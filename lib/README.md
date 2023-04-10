# CPS libraries
## Summary
- `cps` - common functions used by other libraries
- `accel` - MPU-6050 accelerometer library
- `cam` - Raspberry PI Camera library
- `dist` - US-100 Distance sensor library 
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

## Doxygen
Doxygen can be used to present the in-code documentation in a more sophisticated way. To use Doxygen:
1. Download Doxygen according to the instructions on [doxygen.nl/download.html](https://www.doxygen.nl/download.html).
2.  Clone this repository and navigate to this folder.
3.  Run `doxygen Doxyfile`.

HTML-files will be created that can be navigated in the brower.