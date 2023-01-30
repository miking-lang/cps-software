#define IMAGE_SIZE 640*480*3

int cam_init(int* sock, int* client_fd);
void cam_get_image(int sock, char* res);
int cam_close(int client_fd);