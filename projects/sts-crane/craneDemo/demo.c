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
#define TIMEOUT 175 

int file;

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
    setPWM(file, 13, 0, 290); // First servo at 90 degrees
    setPWM(file, 14, 0, 290); // Second servo at 90 degrees
    setPWM(file, 12, 0, 350); // Third servo at 90 degrees
    setPWM(file, 15, 0, 350); // Fourth servo at 90 degrees
}

void unlockHeadBlockServos(){
    setPWM(file, 13, 0, 85); // First servo at 0 degrees
    setPWM(file, 14, 0, 85); // Second servo at 0 degrees
    setPWM(file, 12, 0, 150); // Third servo at 0 degrees
    setPWM(file, 15, 0, 160); // Fourth servo at 0 degrees
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
    movedata_t moveData = {DRIVER_ID, 100*speed, 100};
    CPS_ERR_CHECK(dxl_servo_move_duration(moveData));
}

void moveSkewerSafe(int speed){
    cps_err_t ret;
    movedata_t moveData = {SKEWER_ID, 10*speed, 100};
    CPS_ERR_CHECK(dxl_servo_move_duration(moveData));
}

void moveTrolleySafe(int speed){
    cps_err_t ret;
    movedata_t moveData = {BACK_SERVO_ID, 100*speed, 200};
    CPS_ERR_CHECK(dxl_servo_move_duration(moveData));
}

void moveWheelsSafe(int speed){
    cps_err_t ret;
    uint32_t position = 200*speed;
    uint32_t duration = 200;
    movedata_t moveData[] = {{BACK_WHEELS_ID, position, duration}, {FRONT_WHEELS_ID, position, duration}};
    CPS_ERR_CHECK(dxl_servo_move_many_duration(moveData, 2));
}

void initServos(){
    cps_err_t ret;
    uint32_t pos;
    uint8_t driveMode;

    CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));

    for(int id = 1; id <= 5; id++) {
        CPS_ERR_CHECK(dxl_disable_torque(id));
        CPS_ERR_CHECK(dxl_set_operating_mode(id, DXL_EXTENDED_POSITION_CONTROL));
        CPS_ERR_CHECK(dxl_get_current_position(id, &pos));
        CPS_ERR_CHECK(dxl_set_drive_mode_safe(id, DXL_TIME_PROFILE));
        CPS_ERR_CHECK(dxl_set_profile_acceleration(id, 0));

        CPS_ERR_CHECK(dxl_enable_torque(id));
        CPS_ERR_CHECK(dxl_get_drive_mode(id, &driveMode));
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

int main(){
    initNcurses();

    initServos();

    initI2C();

    int breakLoop = 0;
    int32_t lastKey = 0;
    clock_t lastKeyPressTime = 0;
    float result;
    cps_accel_t acc;
    cps_err_t ret;

    int speed = 1;

    // Create a new window for double-buffering
    WINDOW *buffer = newwin(0, 0, 0, 0);

    CPS_ERR_CHECK(cps_accel_init(&acc, "/dev/i2c-1", 0x68, ACC_SCALE_2_G, GYRO_SCALE_2000_DEG));

    while(1){
        int key = getch();
        werase(buffer);  // Erase the memory buffer

        if(key != ERR) {  // If a key is pressed...
            lastKey = key;  // ...update the last key pressed...
            lastKeyPressTime = clock();  // ...and the last keypress time.
        }

        // If enough time has passed since the last keypress of the same key, treat it as a key release event.
        if(clock() - lastKeyPressTime > TIMEOUT * CLOCKS_PER_SEC / 1000) {
            lastKey = ERR;
        }

        switch(lastKey){
            case('z'): {               //Exit loop
                breakLoop = 1;
                break;
            }
            case(ERR) : {           //No key was pressed
                wprintw(buffer, "Not moving anything\n");
                break;
            }
            case('1') : {           //Activate high speed mode
                speed = 1;
                lastKey = ERR;
                break;
            }   
            case('2'): {
                speed = 2;
                lastKey = ERR;
                break;
            }
            case('3'): {
                speed = 3;
                lastKey = ERR;
                break;
            }
            case('4'): {
                speed = 4;
                lastKey = ERR;
                break;
            }
            case('5'): {
                speed = 5;
                lastKey = ERR;
                break;
            }
            case('a'): {                //Driver up
                wprintw(buffer, "Moving driver servo downwards\n");
                moveDriverSafe(-speed);
                break;
            }
            case('q'): {                //Driver down
                wprintw(buffer, "Moving driver servo upwards\n");
                moveDriverSafe(speed);
                break;
            }   
            case('w'): {
                wprintw(buffer, "Moving skewer counter-clockwise\n");
                moveSkewerSafe(speed);
                break;
            }
            case('s') : {
                wprintw(buffer, "Moving skewer clockwise\n");
                moveSkewerSafe(-speed);
                break;
            }
            case(KEY_UP): {          // Arrow up, trolley forward
                wprintw(buffer, "Moving trolley backwards\n");
                moveTrolleySafe(speed);
                break;
            }
            case(KEY_DOWN): { // Arrow down, trolley backward
                wprintw(buffer, "Moving trolley forwards\n");
                moveTrolleySafe(-speed);
                break;
            }
            case(KEY_RIGHT): {     // Arrow right, wheels right
                wprintw(buffer, "Moving crane right\n");
                moveWheelsSafe(-speed);
                break; 
            }
            case(KEY_LEFT): {     // Arrow left, wheels left
                wprintw(buffer, "Moving crane left\n");
                moveWheelsSafe(speed);
                break;
            }
            case('m'): {        //Unlock mg90s servos
                wprintw(buffer, "Unlocking twistlocks\n");
                unlockHeadBlockServos();
                lastKey = ERR;
                usleep(100000);
                break;
            }
            case('n'): {
                wprintw(buffer, "Locking twistlocks\n");
                lockHeadBlockServos();
                lastKey = ERR;
                usleep(100000);
                break;
            }             
        }

        wprintw(buffer, "Speed: %d\n", speed);

        //Read accelerometer values
        CPS_ERR_CHECK(cps_accel_read_accel(&acc, ACC_DIR_X, &result));
		wprintw(buffer, "acc x: % 2.3f", result);

		CPS_ERR_CHECK(cps_accel_read_angle(&acc, ACC_DIR_X, &result));
		wprintw(buffer, " | ang x: % 2.3f", result);

		/* same, this time for y */
		CPS_ERR_CHECK(cps_accel_read_accel(&acc, ACC_DIR_Y, &result));
		wprintw(buffer, " | acc y: % 2.3f", result);

		CPS_ERR_CHECK(cps_accel_read_angle(&acc, ACC_DIR_Y, &result));
		wprintw(buffer, " | ang y: % 2.3f", result);

		/* and for z */
		CPS_ERR_CHECK(cps_accel_read_accel(&acc, ACC_DIR_Z, &result));
		wprintw(buffer, " | acc z: % 2.3f\n", result);


        mvwprintw(buffer, 10, 0, "->  : Move crane right \n <- : Move crane left\n\n v  : Move trolley towards you \n ^  : Move trolley away from you \n\n q  : Move headblock up \n a  : Move headblock down \n\n w  : Skew headblock clockwise \n s  : Skew headblock counter-clockwise \n\n n  : Unlock twistlocks \n m  : Lock twistlocks\n\n1-5 : Change speed\n\nz   : Exit program\n");

        // Some delay to see the screen
        wrefresh(buffer);

        usleep(100); // sleep for 0.01s
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