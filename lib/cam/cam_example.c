#include "cam_client.h"
#include <sys/time.h>
#include <stdio.h>
#include <string.h>

//compile with gcc cam_example.c cam_client.c -o cam.out

long long get_current_time_with_ms (void) {
    struct timeval te;
    gettimeofday(&te, NULL); // get current time
    long long milliseconds = te.tv_sec*1000LL + te.tv_usec/1000;
    return milliseconds;
}

void alternating(void) {
    int sock, client_fd;
    if (cam_init("193.10.37.141", &sock, &client_fd) == -1) {
        printf("can not initiate camera\n");
        return;
    }
    char buffer[IMAGE_SIZE] = { 0 };
    FILE* fp;
    char ind[4];
    long long starttime = get_current_time_with_ms();
    for (int i = 1; i <= 10; i++) { //Takes 10 images and stores them in files
        if (i % 2 == 0) {
            //Takes about 30 ms with 128*128 resolution. 130 ms with 640*480
            if (cam_get_image(sock, PNG, buffer) == -1) {
                printf("Invalid file format: png\n");
                return;
            }
        }
        else {
            //Takes about 30 ms with 128*128 resolution. 130 ms with 640*480
            if (cam_get_image(sock, BMP, buffer) == -1) {
                printf("Invalig file format: bmp\n");
                return;
            }
        }
        sprintf(ind, "%d", i);
        char filename[20] = "file_";
        strcat(filename, ind);
        if (i % 2 == 0) {
            strcat(filename, ".png");
        }
        else {
            strcat(filename, ".bmp");
        }
	    fp = fopen (filename, "w+");
        printf("saved %s\n", filename);
	    fwrite(buffer, 1, IMAGE_SIZE, fp);
    }
    printf("time: %lld\n", (get_current_time_with_ms() - starttime));
    fclose(fp);

    // closing the connected socket
	cam_close(client_fd);
}

void save_bmp() {
    int sock, client_fd;
    if (cam_init("193.10.37.141", &sock, &client_fd) == -1) {
        printf("can not initiate camera\n");
        return;
    }
    char buffer[IMAGE_SIZE] = { 0 };
    FILE* fp;

    // Takes about 30 ms with 128*128 resolution. 130 ms with 640*480
    if (cam_get_image(sock, BMP, buffer) == -1) {
        printf("Invalig file format: bmp\n");
        return;
    }

    fp = fopen("image.bmp", "w+");
    printf("saved %s\n", "image.bmp");
	fwrite(buffer, 1, IMAGE_SIZE, fp);

    fclose(fp);

    // closing the socket connection
	cam_close(client_fd);
}

int main(int argc, char const* argv[]) {

    // Uncomment one of these to test the camera.
    save_bmp();
    // alternating();
    return 0;
}
