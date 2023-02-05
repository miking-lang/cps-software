#define IMAGE_SIZE 49206 //128*128*3+54

typedef enum {
    PNG = 0,
    BMP,
} cam_img_format;

/**
 * @brief Connects to the server side.
 * 
 * @param cam_ip IP of camera server (Raspberry Pi)
 * @param[out] sock storage for tcp socket
 * @param[out] client_fd storage for client file descriptor
 * 
 * @retval -1 error, see output in terminal
 */
int cam_init(char* cam_ip, int* sock, int* client_fd);

/**
 * @brief Gets image in specified format with 128x128 pixels.
 * 
 * @param sock tcp socket
 * @param[out] format format of the returned image
 * @param[out] res storage for image
 * 
 * @retval -1 error, invalid file format
 */
int cam_get_image(int sock, cam_img_format format, char* res);

/**
 * @brief Closes the server connection
 * 
 * @param client_fd client file descriptor
 * @return output of sockets close funciton
 */
int cam_close(int client_fd);