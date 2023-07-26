#include "dxl.h"
#include "accel.h"

#include <ncurses.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <i2c/smbus.h>  // Include this for i2c_smbus_* functions
#include <stdint.h>  // Include this for uint8_t

#define I2C_ADDR 0x40 // Put here the I2C address of your PCA9685
#define PWM_FREQ 50 // Frequency of PWM signals. In Hz. MG90s operates at 50Hz
#define PCA9685_MODE1 0x00
#define PCA9685_PRESCALE 0xFE

#define FRONT_WHEELS_ID 1
#define BACK_WHEELS_ID 2
#define BACK_SERVO_ID 3
#define DRIVER_ID 4
#define SKEWER_ID 5

#define WHEELS_MIN -6500 // Right limit. Recalibrate after crane is put on rail.
#define WHEELS_MAX 9300 // Left limit. Recalibrate after crane is put on rail.
#define BACK_SERVO_MIN -4200 // Front limit.
#define BACK_SERVO_MAX 15500 // Back limit.
#define DRIVER_MIN -7000 // Lower limit.
#define DRIVER_MAX 20000 // Upper limit.
#define SKEWER_MIN 2000 // Clockwise limit.
#define SKEWER_MAX 2400 // Counter-clockwise limit.

#define TWISTLOCK1_LOCKED 85
#define TWISTLOCK2_LOCKED 85
#define TWISTLOCK3_LOCKED 150
#define TWISTLOCK4_LOCKED 160
#define TWISTLOCK1_UNLOCKED 290
#define TWISTLOCK2_UNLOCKED 290
#define TWISTLOCK3_UNLOCKED 350
#define TWISTLOCK4_UNLOCKED 350
#define TWISTLOCK_STEPS 30

#define WHEELS_SPEED_SCALE 20
#define BACK_SERVO_SPEED_SCALE 10
#define DRIVER_SPEED_SCALE 12
#define SKEWER_SPEED_SCALE 1

#define WHEELS_ACC 500
#define BACK_SERVO_ACC 500
#define DRIVER_ACC 300
#define SKEWER_ACC 200

int file;
int twistlocks_locked = false;

void setPWMFreq(int file, int freq) {
    int prescale = (int)(25000000.0f / (4096 * freq) - 0.5f);
    uint8_t oldmode = i2c_smbus_read_byte_data(file, PCA9685_MODE1);
    uint8_t newmode = (oldmode & 0x7F) | 0x10; // sleep

    i2c_smbus_write_byte_data(file, PCA9685_MODE1, newmode); // go to sleep
    i2c_smbus_write_byte_data(file, PCA9685_PRESCALE, prescale); // set the prescaler
    i2c_smbus_write_byte_data(file, PCA9685_MODE1, oldmode);
    usleep(5000);
    i2c_smbus_write_byte_data(file, PCA9685_MODE1, oldmode | 0x80);
}

void setPWM(int file, int channel, int on, int off) {
    i2c_smbus_write_byte_data(file, 0x06 + 4 * channel, on & 0xFF);
    i2c_smbus_write_byte_data(file, 0x07 + 4 * channel, on >> 8);
    i2c_smbus_write_byte_data(file, 0x08 + 4 * channel, off & 0xFF);
    i2c_smbus_write_byte_data(file, 0x09 + 4 * channel, off >> 8);
}

void lockHeadBlockServos(){
    if (!twistlocks_locked) {
        // Set servos from 0 to 90 degrees
        for (float i = 0; i <= TWISTLOCK_STEPS; i++) {
            setPWM(file, 13, 0, TWISTLOCK1_UNLOCKED * ((TWISTLOCK_STEPS-i)/TWISTLOCK_STEPS) + TWISTLOCK1_LOCKED * (i/TWISTLOCK_STEPS));
            setPWM(file, 14, 0, TWISTLOCK2_UNLOCKED * ((TWISTLOCK_STEPS-i)/TWISTLOCK_STEPS) + TWISTLOCK2_LOCKED * (i/TWISTLOCK_STEPS));
            setPWM(file, 12, 0, TWISTLOCK3_UNLOCKED * ((TWISTLOCK_STEPS-i)/TWISTLOCK_STEPS) + TWISTLOCK3_LOCKED * (i/TWISTLOCK_STEPS));
            setPWM(file, 15, 0, TWISTLOCK4_UNLOCKED * ((TWISTLOCK_STEPS-i)/TWISTLOCK_STEPS) + TWISTLOCK4_LOCKED * (i/TWISTLOCK_STEPS));
            usleep(30000);
        }
        twistlocks_locked = true;
        usleep(100000);
    }
}

void unlockHeadBlockServos(){
    if (twistlocks_locked) {
        // Set servos from 90 to 0 degrees
        for (float i = 0; i <= TWISTLOCK_STEPS; i++) {
            setPWM(file, 13, 0, TWISTLOCK1_LOCKED * ((TWISTLOCK_STEPS-i)/TWISTLOCK_STEPS) + TWISTLOCK1_UNLOCKED * (i/TWISTLOCK_STEPS));
            setPWM(file, 14, 0, TWISTLOCK2_LOCKED * ((TWISTLOCK_STEPS-i)/TWISTLOCK_STEPS) + TWISTLOCK2_UNLOCKED * (i/TWISTLOCK_STEPS));
            setPWM(file, 12, 0, TWISTLOCK3_LOCKED * ((TWISTLOCK_STEPS-i)/TWISTLOCK_STEPS) + TWISTLOCK3_UNLOCKED * (i/TWISTLOCK_STEPS));
            setPWM(file, 15, 0, TWISTLOCK4_LOCKED * ((TWISTLOCK_STEPS-i)/TWISTLOCK_STEPS) + TWISTLOCK4_UNLOCKED * (i/TWISTLOCK_STEPS));
            usleep(30000);
        }
        twistlocks_locked = false;
        usleep(100000);
    }
}

void disableHeadBlockServos(){
    setPWM(file, 12, 0, 0);
    setPWM(file, 13, 0, 0);
    setPWM(file, 14, 0, 0);
    setPWM(file, 15, 0, 0);
}

void initI2C(){
    char filename[20];

    snprintf(filename, 19, "/dev/i2c-1");
    file = open(filename, O_RDWR);
    if (file < 0) {
        printf("Failed to open bus.\n");
        exit(1);
    }

    if (ioctl(file, I2C_SLAVE, I2C_ADDR) < 0) {
        printf("Failed to acquire bus access or talk to slave.\n");
        exit(1);
    }

    setPWMFreq(file, PWM_FREQ);
}

void moveDriverSafe(int speed){
    cps_err_t ret;
    movedata_vel_t moveData = {DRIVER_ID, DRIVER_SPEED_SCALE*speed};
    CPS_ERR_CHECK(dxl_servo_move_duration_velMode(moveData));
}

void moveSkewerSafe(int speed){
    cps_err_t ret;
    movedata_vel_t moveData = {SKEWER_ID, SKEWER_SPEED_SCALE*speed};
    CPS_ERR_CHECK(dxl_servo_move_duration_velMode(moveData));
}

void moveTrolleySafe(int speed){
    cps_err_t ret;
    movedata_vel_t moveData = {BACK_SERVO_ID, BACK_SERVO_SPEED_SCALE*speed};
    CPS_ERR_CHECK(dxl_servo_move_duration_velMode(moveData));
}

void moveWheelsSafe(int speed){
    cps_err_t ret;
    uint32_t velocity = WHEELS_SPEED_SCALE*speed;
    movedata_vel_t moveData[] = {{BACK_WHEELS_ID, velocity}, {FRONT_WHEELS_ID, velocity}};
    CPS_ERR_CHECK(dxl_servo_move_many_duration_velMode(moveData, 2));
}

void initServos(){
    cps_err_t ret;

    CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));

    for(int id = 1; id <= 5; id++) {
        CPS_ERR_CHECK(dxl_disable_torque(id));
    }

    CPS_ERR_CHECK(dxl_set_profile_acceleration(FRONT_WHEELS_ID, WHEELS_ACC));
    CPS_ERR_CHECK(dxl_set_profile_acceleration(BACK_WHEELS_ID, WHEELS_ACC));
    CPS_ERR_CHECK(dxl_set_profile_acceleration(BACK_SERVO_ID, BACK_SERVO_ACC));
    CPS_ERR_CHECK(dxl_set_profile_acceleration(DRIVER_ID, DRIVER_ACC));
    CPS_ERR_CHECK(dxl_set_profile_acceleration(SKEWER_ID, SKEWER_ACC));

    for(int id = 1; id <= 5; id++) {
        CPS_ERR_CHECK(dxl_set_drive_mode_safe(id, DXL_TIME_PROFILE));
        CPS_ERR_CHECK(dxl_set_operating_mode(id, DXL_VELOCITY_CONTROL));
        CPS_ERR_CHECK(dxl_set_profile_acceleration(id, 500));
        CPS_ERR_CHECK(dxl_enable_torque(id));
    }
}

void initNcurses(){
    // Initialize ncurses
    initscr();
    // Disable line buffering, immediately fetch keystrokes
    raw();
    // Enable function keys, arrows, etc.
    keypad(stdscr, TRUE);
    // Don't echo() while we do getch
    noecho();
    // Hide cursor
    curs_set(0);
    // Enable non-blocking input
    nodelay(stdscr, TRUE);

    //Reduce delay for escape keys
    set_escdelay(25);
}

void moveOperation(int32_t operation, int speed) {
    switch(operation){
        case('q'): { // Driver up
            moveDriverSafe(speed);
            break;
        }
        case('a'): { // Driver down
            moveDriverSafe(-speed);
            break;
        }
        case('w'): { // Skew counter-clockwise
            moveSkewerSafe(speed);
            break;
        }
        case('s') : { // Skew clockwise
            moveSkewerSafe(-speed);
            break;
        }
        case(KEY_UP): { // Arrow up, trolley forward
            moveTrolleySafe(speed);
            break;
        }
        case(KEY_DOWN): { // Arrow down, trolley backward
            moveTrolleySafe(-speed);
            break;
        }
        case(KEY_RIGHT): { // Arrow right, wheels right
            moveWheelsSafe(-speed);
            break;
        }
        case(KEY_LEFT): { // Arrow left, wheels left
            moveWheelsSafe(speed);
            break;
        }
    }
}

bool withinLimits(int32_t operation) {
    cps_err_t ret;
    uint32_t position;
    switch(operation) {
        case('q'): { //Driver up
            CPS_ERR_CHECK(dxl_get_current_position(DRIVER_ID, &position));
            return ((int)(position) <= DRIVER_MAX);
        }
        case('a'): { //Driver down
            CPS_ERR_CHECK(dxl_get_current_position(DRIVER_ID, &position));
            return ((int)(position) >= DRIVER_MIN);
        }
        case('w'): {
            CPS_ERR_CHECK(dxl_get_current_position(SKEWER_ID, &position));
            return ((int)(position) <= SKEWER_MAX);
        }
        case('s') : {
            CPS_ERR_CHECK(dxl_get_current_position(SKEWER_ID, &position));
            return ((int)(position) >= SKEWER_MIN);
        }
        case(KEY_UP): {          // Arrow up, trolley forward
            CPS_ERR_CHECK(dxl_get_current_position(BACK_SERVO_ID, &position));
            return ((int)(position) <= BACK_SERVO_MAX);
        }
        case(KEY_DOWN): { // Arrow down, trolley backward
            CPS_ERR_CHECK(dxl_get_current_position(BACK_SERVO_ID, &position));
            return ((int)(position) >= BACK_SERVO_MIN);
        }
        case(KEY_RIGHT): {     // Arrow right, wheels right
            CPS_ERR_CHECK(dxl_get_current_position(FRONT_WHEELS_ID, &position));
            return ((int)(position) >= WHEELS_MIN);
        }
        case(KEY_LEFT): {     // Arrow left, wheels left
            CPS_ERR_CHECK(dxl_get_current_position(FRONT_WHEELS_ID, &position));
            return ((int)(position) <= WHEELS_MAX);
        }
    }
    return false;
}

void print_operation(int32_t operation, WINDOW *buffer) {
    switch(operation){
        case(0): {
            wprintw(buffer, "Not moving anything\n");
            break;
        }
        case('q'): {
            wprintw(buffer, "Moving driver servo upwards\n");
            break;
        }
        case('a'): {
            wprintw(buffer, "Moving driver servo downwards\n");
            break;
        }
        case('w'): {
            wprintw(buffer, "Moving skewer counter-clockwise\n");
            break;
        }
        case('s') : {
            wprintw(buffer, "Moving skewer clockwise\n");
            break;
        }
        case(KEY_UP): {
            wprintw(buffer, "Moving trolley backwards\n");
            break;
        }
        case(KEY_DOWN): {
            wprintw(buffer, "Moving trolley forwards\n");
            break;
        }
        case(KEY_RIGHT): {
            wprintw(buffer, "Moving crane right\n");
            break;
        }
        case(KEY_LEFT): {
            wprintw(buffer, "Moving crane left\n");
            break;
        }
    }
}

int main(){
    cps_err_t ret;
    initNcurses();

    initServos();

    initI2C();

    int32_t ongoingOperation = 0; // start with no operation
    int speed = 1;

    cps_accel_t acc;
    float acc_result;

    // Create a new window for double-buffering
    WINDOW *buffer = newwin(0, 0, 0, 0);

    CPS_ERR_CHECK(cps_accel_init(&acc, "/dev/i2c-1", 0x68, ACC_SCALE_2_G, GYRO_SCALE_2000_DEG));

    bool breakLoop = false;
    while(1){
        int key = getch();
        werase(buffer);  // Erase the memory buffer

        if(key == ERR) { // If no key is pressed
            if (ongoingOperation != 0 && !withinLimits(ongoingOperation)) {
                moveOperation(ongoingOperation, 0);
                ongoingOperation = 0;
            }
        }
        else if (key >= '1' && key <= '9') {
            speed = key - '0';
        }
        else if (key == 'a' || key == 'q' || key == 'w' || key == 's' || key == KEY_UP || key == KEY_DOWN || key == KEY_RIGHT || key == KEY_LEFT) {
            moveOperation(ongoingOperation, 0);
            if (key != ongoingOperation && withinLimits(key)) {
                moveOperation(key, speed);
                ongoingOperation = key;
            }
            else {
                ongoingOperation = 0;
            }
        }
        else if (key == 'z') { //Exit loop
            breakLoop = true;
            moveOperation(ongoingOperation, 0);
            unlockHeadBlockServos();
            ongoingOperation = 0;
        }
        else if (key == 'm') {        //Unlock mg90s servos
            wprintw(buffer, "Unlocking twistlocks\n");
            unlockHeadBlockServos();
        }
        else if (key == 'n') {
            wprintw(buffer, "Locking twistlocks\n");
            lockHeadBlockServos();
        }
        print_operation(ongoingOperation, buffer);

        wprintw(buffer, "Speed: %d\n", speed);

        //Read accelerometer values
        CPS_ERR_CHECK(cps_accel_read_accel(&acc, ACC_DIR_X, &acc_result));
		wprintw(buffer, "acc x: % 2.3f", acc_result);

		CPS_ERR_CHECK(cps_accel_read_angle(&acc, ACC_DIR_X, &acc_result));
		wprintw(buffer, " | ang x: % 2.3f", acc_result);

		/* same, this time for y */
		CPS_ERR_CHECK(cps_accel_read_accel(&acc, ACC_DIR_Y, &acc_result));
		wprintw(buffer, " | acc y: % 2.3f", acc_result);

		CPS_ERR_CHECK(cps_accel_read_angle(&acc, ACC_DIR_Y, &acc_result));
		wprintw(buffer, " | ang y: % 2.3f", acc_result);

		/* and for z */
		CPS_ERR_CHECK(cps_accel_read_accel(&acc, ACC_DIR_Z, &acc_result));
		wprintw(buffer, " | acc z: % 2.3f\n", acc_result);

        mvwprintw(buffer, 10, 0, "->  : Move crane right \n <- : Move crane left\n\n v  : Move trolley towards you \n ^  : Move trolley away from you \n\n q  : Move headblock up \n a  : Move headblock down \n\n w  : Skew headblock counter-clockwise \n s  : Skew headblock clockwise \n\n n  : Lock twistlocks \n m  : Unlock twistlocks\n\n1-9 : Change speed\n\nz   : Exit program\n");

        // Some delay to see the screen
        wrefresh(buffer);

        usleep(10000); // sleep for 0.0001s
        if(breakLoop) break;
    }

    //Disable the headblock servos
    disableHeadBlockServos();

    //Delete window buffer
    delwin(buffer);

    // Cleanup ncurses
    endwin();

    //Close I2C channel
    close(file);

    return 0;
}