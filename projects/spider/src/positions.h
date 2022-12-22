

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

// #define CMD_DELAYDBG
#define CMD_DELAYDBG CMD_DELAY

#define HEIGHT 600

cmd_t base_position[] = {
    /* lay limbs flat */
    CMD_INPUT("lay limbs flat"),
    CMD_MOVE_SYNC_ABS(
        {FL_ROTATE_SHOULDER,     2048,  1000},
        {FR_ROTATE_SHOULDER,     2048,  1000},
        {BL_ROTATE_SHOULDER,     2048,  1000},
        {BR_ROTATE_SHOULDER,     2048,  1000},

        {FL_LIFT_SHOULDER,       2110,  1000},
        {FR_LIFT_SHOULDER,       2120,  1000},
        {BL_LIFT_SHOULDER,       2125,  1000},
        {BR_LIFT_SHOULDER,       2110,  1000},

        {FL_ELBOW,               2048,  1000},
        {FR_ELBOW,               1950,  1000},
        {BL_ELBOW,               2150,  1000},
        {BR_ELBOW,               2048,  1000},
    ),
    CMD_DELAYDBG(1000),
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
    CMD_DELAYDBG(1300)
};

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

cmd_t lift_FR_ELBOW[] = {
    CMD_INPUT("lift FR_ELBOW"),
    CMD_MOVE_SYNC_REL(
        {FR_ELBOW,               300, 4000},
    ),
    CMD_DELAYDBG(1000),
};