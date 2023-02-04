#define IMAGE_SIZE 49206 //128*128*3+54

int cam_init(char* cam_ip, int* sock, int* client_fd);

//Returns -1 if invalid file format
int cam_get_image(int sock, char* res, const char* format);
int cam_close(int client_fd);