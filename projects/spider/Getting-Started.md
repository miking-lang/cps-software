## Introduction
The spider robot has four limbs, each containing three segments -- shoulder rotation, shoulder lifting and elbow, totalling 12 servos. It also has an accelerometer, a distance sensor and a camera module.

**TODO** link to image/schematic?

This guide will explain and provide several examples of spider control.
This guide applies to the `dev` branch of `cps-software` repository. It can be found at https://github.com/miking-lang/cps-software/tree/dev.

## Physical Setup
Make sure the working area around the spider is clean! You can gauge the area by rotating the limbs around the shoulder joints while stretched out.

The following items are required:
1. 12v, min 5A power supply (marked `PS-12V-5A`)
2. 5v, min 3A power supply with a USB-C connector
3. Micro-USB cable (at least 0.5m)
4. Raspberry Pi

The Raspberry Pi is to be powered with the 5V power supply. The required power supply should already be connected to the RPi.

The RPi is to be connected to the controller board via the Micro-USB cable. The controller board is located on the spider, between the top and the bottom plates.

The controller board is to be powered with the 12v power supply. The existing power supply (a black brick marked `PS-12V-5A`) may prove inadequate if all 12 servos are to be moved at once. If more power is required, make use of a provided LiPo battery. Make sure to follow all the safety precations of working with LithiumIon batteries.

The controller board has a toggle switch to turn the power on or off. The switch must be in the ON position during usage, and in the OFF position while not in use.

## Getting Started
All robot control is done from the attached Raspberry Pi. Login credentials and the IP address can be found on Slack.
```bash
# login to RPi
ssh <user>@<host>

# obtain latest sources (dev branch)
cd /tmp
git clone -b dev git@github.com:miking-lang/cps-software.git
# nagivate to the demo folder
cd cps-software/projects/spider/demo
```

### Environment Overview
The following folder layout is used for the spider source code:
```bash
demo/
    CMakeLists.txt
    src/
        main.c
        ctrl.c
        ctrl.h
        positions.h
```

### Build System
CMake is used as the build system. The following process is used to build the demo for the first time:
```bash
# nagivate to demo/ (contains CMakeLists.txt and src/)
mkdir build
cd build
cmake ..
make
```

To rebuild:
```bash
# navigate to demo/build/
make
```

### Example Code
`demo/src/main.c` contains example code to either have the spider do pushups or perform a wave. Select which action to perform by uncommenting the corresponding function call in `main.c`. See Appendix A for a line-by-line explanation of the code.

The positions are defined in `demo/src/positions.h` and are a sequence of commands to move specific servos. See Appendix B for an explanation of how these are structured.

### Prompts
The movements described in `positions.h` have `CMD_INPUT` after each movement. This is to allow the user to step through the movements one by one, in order to insure nothing goes wrong or to debug issues. To step through the movements, simply press `ENTER` after each prompt.

### Running the Code
Before running the generated executable, a few physical things need to be taken into account:
1. The spider needs to reside on a flat, firm surface.
2. The area around the spider is clear
3. It is preferable to have its limbs already flat, to prevent excessive scraping.
4. The controller must be connected via USB to the RaspberryPi.
5. The controller must be supplied with external power.
6. The controller must be turned on (via an onboard switch).

To execute:
```bash
# navigate to demo/build/
./spider
```

If the program fails, or the expected movement is not observed, please carefully check the steps above again. Common failure points include not connecting USB or external power.

### Results
If everything went well, this should have resulted in the spider performing the selected action (either pushups or a wave).

Note that after the program is done, the limbs stay fixed in their place, and cannot be moved. This is due to the motors still being powered on, and attempting to keep their present position. While they can be shut off before program shutdown by calling `dxl_disable_torque(1..12)`, this will result in them being unable to support the spider's weight if it is e.g. standing. To avoid collapse of the whole structure, during development it is recommended to leave torque on.

An easy way to turn off the torque and allow manual locomotion of the limbs, is to cycle the external power switch on the controller board.

### Error Handling and Return Values
All libraries within CPS utilize the same error handling strategy -- if a function can encounter an error during execution, it will be returned as the return value. If `CPS_ERR_OK` is returned, no error occurred.
If a function needs to return one or more values, they will be returned through pointers given as function arguments.
To easier handle errors during development, the following helper macros are provided:
1. `CPS_ERR_CHECK` -- if `CPS_ERR_OK`, do nothing, else print error location & error name and abort.
2. `CPS_RET_ON_ERR` -- if `CPS_ERR_OK`, do nothing, else return error value from function.
Both of these macros expect a variable available in local scope called `ret` of type `cps_err_t`. Their implementation is available in `cps-software/lib/cps/cps.h`.

#### Example Usage
```c
cps_err_t ret;
CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));
```

## Sensing the World
The spider robot contains two sensors:
1. An accelerometer
2. A distance sensor

Each of those has a corresponding library available in `cps-software/lib/`: `lib/accel` and `lib/dist`.
There is no spider-specific configuration required for these libraries, and they are used as if they were standalone.

**TODO** insert a wiring diagram for connecting accel & dist to RPi.

Example code for both of the sensors is available under `cps-software/lib/examples`. The examples show how to initialize the sensors and handle error conditions. For production code, consider manually handling errors instead of using `CPS_ERR_CHECK`/`CPS_RET_ON_ERR`.

## In-depth on Components
Each library in CPS contains documentation in its header file(s) (located in `cps-software/lib/<library>/<library>.h`). That documentation will eventially be provided in HTML form as an external reference.

## Camera
TBW
