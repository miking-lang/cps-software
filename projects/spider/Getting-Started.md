## Introduction
The spider robot has four limbs, each containing three segments -- shoulder rotation, shoulder lifting and elbow, totalling 12 servos. It also has an accelerometer, a distance sensor and a camera module.
**TODO** link to image/schematic?
This guide will explain and provide several examples of spider control.

This guide applies to the `dev` branch of `cps-software` repository. It can be found at https://github.com/miking-lang/cps-software/tree/dev.

### Appendices Overview
Appendix A contains `ctrl.c` and `ctrl.h`. Those files provide functions for easy synchronous control of several servos.
Appendix B contains some example positions which can be used to get the robot to move. It also contains information on how to utilize those position lists in your code.
Appendix C contains a line-by-line walkthrough of example code to get the spider to lay flat.

## Physical Setup
The Raspberry Pi is to be powered with a 5V power supply with at least 3A of current capability. The required charger should already be connected to the RPi.

The RPi is to be connected to the controller board via a Micro-USB cable. The controller board is located on the spider, between the top and the bottom plates.

The controller board is to be powered with a power supply with a rating of XXXV and at least YYYA of current capability. The existing power supply (a black brick with a short, angled mains adapter) may prove inadequate if all 12 servos are to be moved at once. If more power is required, make use of a provided LiPo battery. Make sure to follow all the safety precations of working with LithiumIon batteries.

The controller board has a toggle switch to turn the power on or off. The switch must be in the ON position during usage, and in the OFF position while not in use.

## Environment Setup
All robot control is done from the attached Raspberry Pi. Login credentials and the IP address can be found on Slack.
On the Raspberry Pi, the source code for `cps-software` is located in the home folder. That can be used, or a new clone of the repository can be made. Make sure to use the `dev` branch!

This guide will utilize the existing `cps-software` repository for the different libraries, but a different directory for the spider source code.

The following folder layout is used for the spider source code:
```bash
spider-demo/
	CMakeLists.txt
	src/
		main.c
		ctrl.c
		ctrl.h
		positions.h
```
`CMakeLists.txt` is provided further below.
`ctrl.c`, `ctrl.h` and `positions.h` are provided in Appendices A & B.
`main.c` is built up over the course of this guide.

## Error Handling and Return Values
All libraries within CPS utilize the same error handling strategy -- if a function can encounter an error during execution, it will be returned as the return value. If `CPS_ERR_OK` is returned, no error occurred.
If a function needs to return one or more values, they will be returned through pointers given as function arguments.
To easier handle errors during development, the following helper macros are provided:
1. `CPS_ERR_CHECK` -- if `CPS_ERR_OK`, do nothing, else print error location & error name and abort.
2. `CPS_RET_ON_ERR` -- if `CPS_ERR_OK`, do nothing, else return error value from function.
Both of these macros expect a variable available in local scope called `ret` of type `cps_err_t`. Their implementation is available in `cps-software/lib/cps/cps.h`.

### Example Usage
```c
cps_err_t ret;
CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));
```

## Getting Started
```bash
# login to RPi
ssh <user>@<host>

# setup the folder structure
mkdir spider-demo
cd spider-demo
mkdir src
```
`CMakeLists.txt` source is provided further below.

The spider's servos are controlled using `cps_dxl` library (located in `cps-software/lib/dxl/`). To begin control:
1. Initialize DynamixelSDK using `dxl_init`
2. Initialize all 12 servos and turn them on
```c
#include "dxl.h"

#define NUM_SERVOS 12

cps_err_t spider_init(void) {
	cps_err_t ret;
	for (int id = 1; id <= NUM_SERVOS; id++) {
		CPS_RET_ON_ERR(dxl_set_drive_mode(id, DXL_TIME_PROFILE));
		CPS_RET_ON_ERR(dxl_enable_torque(id));
	}

	return CPS_ERR_OK;
}

int main(void) {
	cps_err_t ret;
	CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));
	CPS_ERR_CHECK(spider_init());

	return 0;
}
```

The build system utilized for the libraries is `cmake`. The following `CMakeLists.txt` can be used to compile the above code:
`CMakeLists.txt`
```cmake
cmake_minimum_required(VERSION 3.15)

project(SpiderRobot VERSION 1.0)

# Provide the path to cps-software/lib here
set(CPS_LIBRARY_DIR "../cps-software/lib")

add_subdirectory("${CPS_LIBRARY_DIR}/" "cps")

# Spider controller
add_executable(spider
	src/main.c
)
target_compile_options(spider PUBLIC
	-Wall -Wextra -g
)
target_compile_definitions(spider PUBLIC
	LINUX _GNU_SOURCE
)
target_include_directories(spider PUBLIC
	src/
	"${CPS_LIBRARY_DIR}/dxl/"
	"${CPS_LIBRARY_DIR}/accel/"
)
target_link_directories(cps_dxl PUBLIC
	# This is where DynamixelSDK's libraries end up by default
	/usr/local/lib/
)
target_link_libraries(spider PUBLIC
	cps_dxl
	cps_accel
)
```

Compilation is then done as follows:
```bash
# Navigate to the folder containing `CMakeLists.txt` and `src/`
mkdir build
cd build
cmake ..
make
```

With everything set up correctly, the above program should compile without errors.

## Utilizing the Spider Library
The above program is a bare-bones starting point for controlling the spider. Appendix A of this document contains functions for controlling the spider's motions. These functions will be cleaned up and upstreamed into a spider-specific library at later date, and this guide will be updated to reflect that. Currently, to utilize these functions:
1. Save the two files in the `src/` directory
2. Add `ctrl.c` to `CMakeLists.txt`:
```cmake
add_executable(spider
	src/main.c
	src/ctrl.c
)
```
3. Include `ctrl.h` in `main.c` at the top:
```c
#include "dxl.h"
#include "ctrl.h"

...
```

Here is an example of laying the spider's limbs flat. Take note of comments in the source code explaining how commands work. Line-by-line explanation of the program is provided in Appendix C.
```c
#include "dxl.h"
#include "ctrl.h"

#define NUM_SERVOS 12

cps_err_t spider_init(void) {
	cps_err_t ret;
	for (int id = 1; id <= NUM_SERVOS; id++) {
		CPS_RET_ON_ERR(dxl_set_drive_mode(id, DXL_TIME_PROFILE));
		CPS_RET_ON_ERR(dxl_enable_torque(id));
	}

	return CPS_ERR_OK;
}

cmd_t POSITION_LAY[] = {
	// This command will move limbs to their resting positions
	// over the course of 3 seconds.
	// NOTE this is one of the few cases of absolute movement
	CMD_MOVE_SYNC_ABS(
		// {LIMB_ID, POSITION, DURATION}
        {FL_ROTATE_SHOULDER,     2048,  3000},
        {FR_ROTATE_SHOULDER,     2048,  3000},
        {BL_ROTATE_SHOULDER,     2048,  3000},
        {BR_ROTATE_SHOULDER,     2048,  3000},

        {FL_LIFT_SHOULDER,       2110,  3000},
        {FR_LIFT_SHOULDER,       2120,  3000},
        {BL_LIFT_SHOULDER,       2125,  3000},
        {BR_LIFT_SHOULDER,       2110,  3000},

        {FL_ELBOW,               2048,  3000},
        {FR_ELBOW,               1950,  3000},
        {BL_ELBOW,               2150,  3000},
        {BR_ELBOW,               2048,  3000},
    ),
    // Commands are async, so wait for 3 seconds untill
    // all the limb movement has ceased.
	CMD_DELAY(3000),
};

int main(void) {
	cps_err_t ret;
	CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));
	CPS_ERR_CHECK(spider_init());

	// Execute all commands in the array POSITION_LAY
	// cmd_exec(cmds, num_cmds);
	cmd_exec(POSITION_LAY, sizeof(POSITION_LAY)/sizeof(*POSITION_LAY));

	return 0;
}
```

The above code can be compiled using `cmake` process outline further above.

## Running the Code
Before running the generated executable, a few physical things need to be taken into account:
1. The spider needs to reside on a flat, firm surface.
2. It is preferable to have its limbs already flat, to prevent excessive scraping.
3. The controller must be connected via USB to the RaspberryPi.
4. The controller must be supplied with external power.
5. The controller must be turned on (via an onboard switch).

Once all of these are observed, the generated executable may be run as `./spider` from CMake's build directory. If the program fails, or the expected movement is not observed, please carefully check the steps above again. Common failure points include not connecting USB or external power.

## Results
If everything went well, this should have resulted in the spider aligning its limbs to lay flat on the underlying surface (or, more likely, hovering slightly above it).
Note that after the program is done, the limbs stay fixed in their place, and cannot be moved. This is due to the motors still being powered on, and attempting to keep their present position. While they can be shut off before program shutdown by calling `dxl_disable_torque(1..12)`, this will result in them being unable to support the spider's weight if it is e.g. standing. To avoid collapse of the whole structure, during development it is recommended to leave torque on.
An easy way to turn off the torque and allow manual locomotion of the limbs, cycle the external power switch on the controller board.

## More Movements
Appendix B contains movement information for several actions:
1. Standing up, waving and laying down
2. Doing pushups

Appendix B also contains the required C code to execute those actions.

## Sensing the World
The spider robot contains two sensors:
1. An accelerometer
2. A distance sensor

Each of those has a corresponding library available in `cps-software/lib/`: `lib/accel` and `lib/dist`.
There is no spider-specific configuration required for these libraries, and they are used as if they were standalone.

**TODO** insert a wiring diagram for connecting accel & dist to RPi. ask Frej for details

Example code for both of the sensors is available under `cps-software/lib/examples`. The examples show how to initialize the sensors and handle error conditions. For production code, consider manually handling errors instead of using `CPS_ERR_CHECK`/`CPS_RET_ON_ERR`.

## In-depth on Components
Each library in CPS contains documentation in its header file(s) (located in `cps-software/lib/<library>/<library>.h`). That documentation will eventially be provided in HTML form as an external reference.

## Camera
TBW

## Appendix A
`ctrl.c`:
```c
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>

#include "dxl.h"
#include "ctrl.h"

/**
 * Uses the time.h function nanosleep to sleep for tms milliseconds.
 * 
 * @param tms milliseconds to sleep
 * @return int 0 on successfully sleeping for tms milliseconds, -1 otherwise. errno is set to indicate the error.
 */
int msdelay(long tms) {
    struct timespec ts;
    int ret;

    if (tms < 0) {
        errno = EINVAL;
        return -1;
    }

    ts.tv_sec = tms / 1000;
    ts.tv_nsec = (tms % 1000) * 1000000;

    do {
        ret = nanosleep(&ts, &ts);
    } while (ret && errno == EINTR);

    return ret;
}

/**
 * Waits for input before continuing.
 * 
 * Exits the program if q is inserted. Continues with the commands on any other input.
 * 
 * @param prompt message to prompt before waiting for input
 */
void ask_quit(const char *prompt) {
    //return; //uncomment to make it skip waiting for input
    puts(prompt);
    if (getc(stdin) == 'q')
        exit(0);
    return;
}

/**
 * Executes an array of cmd_t commands.
 * 
 * The commands are executed in the order they appear in the array.
 * 
 * @param commands an array of cmd_t commands
 * @param count number of cmd_t commands
 */
void cmd_exec(cmd_t commands[], size_t count) {
    cps_err_t ret;
    for (size_t i = 0; i < count; i++) {
        cmd_t *cmd = &commands[i];
        switch (cmd->cmd_id) {
        case CMD_ID_MOVE_SYNC_ABS: {
            CPS_ERR_CHECK(dxl_servo_move_many_duration_abs((movedata_t *)cmd->argv, cmd->argc));
            break;
        }
        case CMD_ID_MOVE_SYNC_REL:
            CPS_ERR_CHECK(dxl_servo_move_many_duration((movedata_t *)cmd->argv, cmd->argc));
            break;
        case CMD_ID_INPUT:
            ask_quit((const char *)cmd->argv);
            break;
        case CMD_ID_DELAY:
            msdelay(*(size_t*)cmd->argv);
            break;
        default:
            abort();
        }
    }
}
```
`ctrl.h`
```c
#pragma once
typedef enum {
    BR_ROTATE_SHOULDER = 1,
    BR_LIFT_SHOULDER,
    FR_ELBOW,
    FR_ROTATE_SHOULDER,
    BR_ELBOW,
    FR_LIFT_SHOULDER, 
    BL_LIFT_SHOULDER,
    FL_ROTATE_SHOULDER,
    BL_ROTATE_SHOULDER,
    FL_ELBOW,
    FL_LIFT_SHOULDER,
    BL_ELBOW,
} servos;

typedef struct {
    uint8_t cmd_id;
    size_t argc;
    void *argv;
} cmd_t;

enum {
    CMD_ID_MOVE_SYNC_ABS,
    CMD_ID_MOVE_SYNC_REL,
    CMD_ID_INPUT,
    CMD_ID_DELAY,
};

void cmd_exec(cmd_t commands[], size_t count);

#define COUNT_VARARGS(type, _argv...) (sizeof((type[]){_argv})/sizeof(*(type[]){_argv}))
#define CMD_MOVE_SYNC_ABS(_argv...) \
{   .cmd_id = CMD_ID_MOVE_SYNC_ABS, \
    .argc = COUNT_VARARGS(movedata_t, _argv), \
    .argv = &(movedata_t[]){_argv} }

#define CMD_MOVE_SYNC_REL(_argv...) \
{   .cmd_id = CMD_ID_MOVE_SYNC_REL, \
    .argc = COUNT_VARARGS(movedata_t, _argv), \
    .argv = &(movedata_t[]){_argv} }

#define CMD_INPUT(prompt) { \
    .cmd_id = CMD_ID_INPUT, .argv = prompt }

#define CMD_DELAY(ms) { \
    .cmd_id = CMD_ID_DELAY, .argv = (size_t[]){ms} }

// Turn on or off debug-delays
// #define CMD_DELAYDBG
#define CMD_DELAYDBG CMD_DELAY
```

## Appendix B
**NOTE**: some of the command lists below utilize `CMD_INPUT`. This pauses command execution until `ENTER` is pressed, allowing for executing one command at a time and observing results.

To get the spider to stand up and wave:
```c
#include "positions.h"

...

cmd_exec(lay2stand, sizeof(lay2stand)/sizeof(*lay2stand));
cmd_exec(wave_shoulder, sizeof(wave_shoulder)/sizeof(*wave_shoulder));
cmd_exec(stand2lay, sizeof(stand2lay)/sizeof(*stand2lay));
```

To perform a series of pushups (3 in this example):
```c
#include "positions.h"

...

cmd_exec(prepare_push_up, sizeof(prepare_push_up)/sizeof(*prepare_push_up));
for(int i = 0; i < 3; i++){
	cmd_exec(push_up, sizeof(push_up)/sizeof(*push_up));
}
cmd_exec(exit_push_up, sizeof(exit_push_up)/sizeof(*exit_push_up));
```

To use these, don't forget to `#include "positions.h"` at the top of `main.c`.

`positions.h`
```c
#pragma once
#include "ctrl.h"

// How high should the spider raise itself during pushups
#define HEIGHT 600

cmd_t lay2stand[] = {
    /* lay limbs flat */
    CMD_INPUT("lay limbs flat"),
    CMD_MOVE_SYNC_ABS(
        {FL_ROTATE_SHOULDER,     2048,  500},
        {FR_ROTATE_SHOULDER,     2048,  500},
        {BL_ROTATE_SHOULDER,     2048,  500},
        {BR_ROTATE_SHOULDER,     2048,  500},

        {FL_LIFT_SHOULDER,       2110,  500},
        {FR_LIFT_SHOULDER,       2120,  500},
        {BL_LIFT_SHOULDER,       2125,  500},
        {BR_LIFT_SHOULDER,       2110,  500},

        {FL_ELBOW,               2048,  500},
        {FR_ELBOW,               1950,  500},
        {BL_ELBOW,               2150,  500},
        {BR_ELBOW,               2048,  500},
    ),
    CMD_DELAYDBG(500),
    /* raise limbs */
    CMD_INPUT("raise limbs"),
    CMD_MOVE_SYNC_REL(
        {FL_ROTATE_SHOULDER,      200, 1200},
        {FR_ROTATE_SHOULDER,    - 200, 1200},
        {BL_ROTATE_SHOULDER,    - 200, 1200},
        {BR_ROTATE_SHOULDER,      200, 1200},

        {FL_LIFT_SHOULDER,      - 800, 1000},
        {FR_LIFT_SHOULDER,      - 800, 1000},
        {BL_LIFT_SHOULDER,      - 800, 1000},
        {BR_LIFT_SHOULDER,      - 800, 1000},

        {FL_ELBOW,              -1500, 1300},
        {FR_ELBOW,               1500, 1300},
        {BL_ELBOW,               1500, 1300},
        {BR_ELBOW,              -1500, 1300},
    ),
    CMD_DELAYDBG(1300),
    /* lift body */
    CMD_INPUT("lift body"),
    CMD_MOVE_SYNC_REL(
        {FL_LIFT_SHOULDER,        300, 1000},
        {FR_LIFT_SHOULDER,        300, 1000},
        {BL_LIFT_SHOULDER,        300, 1000},
        {BR_LIFT_SHOULDER,        300, 1000},

        {FL_ELBOW,                0, 1000},
        {FR_ELBOW,                0, 1000},
        {BL_ELBOW,                0, 1000},
        {BR_ELBOW,                0, 1000},
    ),
    CMD_DELAYDBG(1000),
    CMD_INPUT("raise"),
    CMD_MOVE_SYNC_REL(
        {FL_LIFT_SHOULDER,        HEIGHT,  800},
        {FR_LIFT_SHOULDER,        HEIGHT,  800},
        {BL_LIFT_SHOULDER,        HEIGHT,  800},
        {BR_LIFT_SHOULDER,        HEIGHT,  800},

        {FL_ELBOW,                HEIGHT, 1000},
        {FR_ELBOW,               -HEIGHT, 1000},
        {BL_ELBOW,               -HEIGHT, 1000},
        {BR_ELBOW,                HEIGHT, 1000},
    ),
    CMD_DELAYDBG(1000),
    CMD_DELAYDBG(1000),
    CMD_INPUT("leg"),
    CMD_MOVE_SYNC_REL(
        {BR_LIFT_SHOULDER, -300, 640},
        {BR_ELBOW, -250, 800},

    ),
    CMD_DELAY(600),
    CMD_MOVE_SYNC_REL(
        {FL_LIFT_SHOULDER, -400, 800},
        {FL_ELBOW, 1400, 1500},
    ),
    CMD_DELAYDBG(1500),
    CMD_INPUT("done"),
    //CMD_DELAYDBG(5000),
};

cmd_t stand2lay[] = {
    CMD_INPUT("un(leg)"),
    CMD_MOVE_SYNC_REL(
        {FL_ELBOW, -1400, 1500},
        {FL_LIFT_SHOULDER, 400, 800},
    ),
    CMD_DELAY(1500),
    CMD_MOVE_SYNC_REL(
        {BR_ELBOW, 250, 1000},
    ),
    CMD_DELAY(200),
    CMD_MOVE_SYNC_REL(
        {BR_LIFT_SHOULDER, 300, 800},
    ),
    CMD_DELAYDBG(800),
    CMD_INPUT("unraise"),
    CMD_MOVE_SYNC_REL(
        {FL_ELBOW,                -HEIGHT, 1000},
        {FR_ELBOW,                 HEIGHT, 1000},
        {BL_ELBOW,                 HEIGHT, 1000},
        {BR_ELBOW,                -HEIGHT, 1000},
    ),
    CMD_DELAY(200),
    CMD_MOVE_SYNC_REL(
        {FL_LIFT_SHOULDER,        -HEIGHT,  800},
        {FR_LIFT_SHOULDER,        -HEIGHT,  800},
        {BL_LIFT_SHOULDER,        -HEIGHT,  800},
        {BR_LIFT_SHOULDER,        -HEIGHT,  800},
    ),
    CMD_DELAYDBG(800),
    CMD_INPUT("un(lift body)"),
    CMD_MOVE_SYNC_REL(
        {FL_LIFT_SHOULDER,        -300, 1000},
        {FR_LIFT_SHOULDER,        -300, 1000},
        {BL_LIFT_SHOULDER,        -300, 1000},
        {BR_LIFT_SHOULDER,        -300, 1000},
        {FL_ELBOW,                  100, 1000},
        {FR_ELBOW,                 -100, 1000},
        {BL_ELBOW,                 -100, 1000},
        {BR_ELBOW,                  100, 1000},
    ),
    CMD_DELAYDBG(1000),
    CMD_INPUT("un(raise limbs)"),
    CMD_MOVE_SYNC_REL(
        {FL_ELBOW,              1500, 1300},
        {FR_ELBOW,             -1500, 1300},
        {BL_ELBOW,             -1500, 1300},
        {BR_ELBOW,              1500, 1300},
    ),
    CMD_DELAY(100),
    CMD_MOVE_SYNC_REL(
        {FL_ROTATE_SHOULDER,    - 100, 1200},
        {FR_ROTATE_SHOULDER,      100, 1200},
        {BL_ROTATE_SHOULDER,      100, 1200},
        {BR_ROTATE_SHOULDER,    - 100, 1200},
    ),
    CMD_DELAY(200),
    CMD_MOVE_SYNC_REL(
        {FL_LIFT_SHOULDER,        800, 1000},
        {FR_LIFT_SHOULDER,        800, 1000},
        {BL_LIFT_SHOULDER,        800, 1000},
        {BR_LIFT_SHOULDER,        800, 1000},
    ),
    CMD_DELAYDBG(1000),
    CMD_INPUT("done")
};

cmd_t wave_shoulder[] = {
    CMD_DELAY(1000),
    CMD_MOVE_SYNC_REL(
        {FL_ROTATE_SHOULDER, 400, 800},
        {FL_ELBOW, -300, 800},
    ),
    CMD_DELAY(1000),
    CMD_MOVE_SYNC_REL(
        {FL_ROTATE_SHOULDER, -400, 800},
        {FL_ELBOW, 300, 800},
    ),
    CMD_DELAY(1000),
};

cmd_t wave_elbow[] = {
 CMD_DELAY(1000),
    CMD_MOVE_SYNC_REL(
        {FL_ELBOW, 300, 800},
    ),
    CMD_DELAYDBG(900),
    CMD_MOVE_SYNC_REL(
        {FL_ELBOW, -300, 800},
    ),
    CMD_DELAYDBG(900),
    CMD_DELAY(1000),
};

cmd_t lay_limbs[] = {
    /* lay limbs flat */
    CMD_INPUT("lay limbs flat"),
    CMD_MOVE_SYNC_ABS(
        {FL_ROTATE_SHOULDER,     2048,  3000},
        {FR_ROTATE_SHOULDER,     2048,  3000},
        {BL_ROTATE_SHOULDER,     2048,  3000},
        {BR_ROTATE_SHOULDER,     2048,  3000},

        {FL_LIFT_SHOULDER,       2110,  3000},
        {FR_LIFT_SHOULDER,       2120,  3000},
        {BL_LIFT_SHOULDER,       2125,  3000},
        {BR_LIFT_SHOULDER,       2110,  3000},

        {FL_ELBOW,               2048,  3000},
        {FR_ELBOW,               1950,  3000},
        {BL_ELBOW,               2150,  3000},
        {BR_ELBOW,               2048,  3000},
    ),
    CMD_DELAYDBG(3000)
};

cmd_t prepare_push_up[] = {
    /* lay limbs flat */
    CMD_INPUT("lay limbs flat"),
    CMD_MOVE_SYNC_ABS(
        {FL_ROTATE_SHOULDER,     2048,  3000},
        {FR_ROTATE_SHOULDER,     2048,  3000},
        {BL_ROTATE_SHOULDER,     2048,  3000},
        {BR_ROTATE_SHOULDER,     2048,  3000},

        {FL_LIFT_SHOULDER,       2110,  3000},
        {FR_LIFT_SHOULDER,       2120,  3000},
        {BL_LIFT_SHOULDER,       2125,  3000},
        {BR_LIFT_SHOULDER,       2110,  3000},

        {FL_ELBOW,               2048,  3000},
        {FR_ELBOW,               1950,  3000},
        {BL_ELBOW,               2150,  3000},
        {BR_ELBOW,               2048,  3000},
    ),
    CMD_DELAYDBG(3000),
    CMD_INPUT("raise limbs"),
    CMD_MOVE_SYNC_REL(
        {FL_ROTATE_SHOULDER,      200, 1200},
        {FR_ROTATE_SHOULDER,    - 200, 1200},
        {BL_ROTATE_SHOULDER,    - 200, 1200},
        {BR_ROTATE_SHOULDER,      200, 1200},

        {FL_LIFT_SHOULDER,      - 800, 1000},
        {FR_LIFT_SHOULDER,      - 800, 1000},
        {BL_LIFT_SHOULDER,      - 800, 1000},
        {BR_LIFT_SHOULDER,      - 800, 1000},

        {FL_ELBOW,              -1500, 1300},
        {FR_ELBOW,               1500, 1300},
        {BL_ELBOW,               1500, 1300},
        {BR_ELBOW,              -1500, 1300},
    ),
    CMD_DELAYDBG(1300),
    /* lift body */
    CMD_INPUT("lift body"),
    CMD_MOVE_SYNC_REL(
        {FL_LIFT_SHOULDER,        310, 1000},
        {FR_LIFT_SHOULDER,        310, 1000},
        {BL_LIFT_SHOULDER,        310, 1000},
        {BR_LIFT_SHOULDER,        310, 1000},

        {FL_ELBOW,                0, 1000},
        {FR_ELBOW,                0, 1000},
        {BL_ELBOW,                0, 1000},
        {BR_ELBOW,                0, 1000},
    ),
    CMD_DELAYDBG(1000),
    /* raise limbs */
};
cmd_t push_up[] = {
    CMD_INPUT("raise"),
    CMD_MOVE_SYNC_REL(
        {FL_LIFT_SHOULDER,        HEIGHT,  600},
        {FR_LIFT_SHOULDER,        HEIGHT,  600},
        {BL_LIFT_SHOULDER,        HEIGHT,  600},
        {BR_LIFT_SHOULDER,        HEIGHT,  600},

        {FL_ELBOW,                HEIGHT, 800},
        {FR_ELBOW,               -HEIGHT, 800},
        {BL_ELBOW,               -HEIGHT, 800},
        {BR_ELBOW,                HEIGHT, 800},
    ),
    CMD_INPUT("unraise"),
    CMD_DELAYDBG(800),
    CMD_MOVE_SYNC_REL(
        {FL_ELBOW,                -HEIGHT, 1000},
        {FR_ELBOW,                 HEIGHT, 1000},
        {BL_ELBOW,                 HEIGHT, 1000},
        {BR_ELBOW,                -HEIGHT, 1000},
    ),
    CMD_DELAY(200),
    CMD_MOVE_SYNC_REL(
        {FL_LIFT_SHOULDER,        -HEIGHT,  800},
        {FR_LIFT_SHOULDER,        -HEIGHT,  800},
        {BL_LIFT_SHOULDER,        -HEIGHT,  800},
        {BR_LIFT_SHOULDER,        -HEIGHT,  800},
    ),
    CMD_DELAYDBG(1300),
    CMD_INPUT("done")
};

cmd_t exit_push_up[] = {
    CMD_INPUT("un(lift body)"),
    CMD_MOVE_SYNC_REL(
        {FL_LIFT_SHOULDER,        -310, 1000},
        {FR_LIFT_SHOULDER,        -310, 1000},
        {BL_LIFT_SHOULDER,        -310, 1000},
        {BR_LIFT_SHOULDER,        -310, 1000},
    ),
    CMD_DELAYDBG(1000),
    CMD_INPUT("un(raise limbs)"),
    CMD_MOVE_SYNC_REL(
        {FL_ELBOW,              1500, 1300},
        {FR_ELBOW,               -1500, 1300},
        {BL_ELBOW,               -1500, 1300},
        {BR_ELBOW,              1500, 1300},
    ),
    CMD_DELAY(100),
    CMD_MOVE_SYNC_REL(
        {FL_ROTATE_SHOULDER,    - 100, 1200},
        {FR_ROTATE_SHOULDER,      100, 1200},
        {BL_ROTATE_SHOULDER,      100, 1200},
        {BR_ROTATE_SHOULDER,    - 100, 1200},
    ),
    CMD_DELAY(200),
    CMD_MOVE_SYNC_REL(
        {FL_LIFT_SHOULDER,        800, 1000},
        {FR_LIFT_SHOULDER,        800, 1000},
        {BL_LIFT_SHOULDER,        800, 1000},
        {BR_LIFT_SHOULDER,        800, 1000},
    ),
    CMD_DELAYDBG(1000),
    CMD_INPUT("done")
};
```

## Appendix C
TBW
