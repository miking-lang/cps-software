#include "cam_client.h"
#include <sys/time.h>
#include <stdio.h>
#include <string.h>

long long get_current_time_with_ms (void) {
    struct timeval te;
    gettimeofday(&te, NULL); // get current time
    long long milliseconds = te.tv_sec*1000LL + te.tv_usec/1000;
    return milliseconds;
}

int main(int argc, char const* argv[]) {
    int sock, client_fd;
    cam_init(&sock, &client_fd);

    char buffer[IMAGE_SIZE] = { 0 };
    FILE* fp;
    char ind[4];
    long long starttime = get_current_time_with_ms();
    printf("starttime: %lld\n", starttime);
    for (int i = 70; i <= 80; i++) { //Takes 10 images and stores them in files
        printf("i: %d\n", i);
        cam_get_image(sock, buffer); //Takes about 130 ms with 640*480
        printf("cam_get_image done\n");
        sprintf(ind, "%d", i);
        char filename[20] = "file_";
        strcat(filename, ind);
        strcat(filename, ".png");
	    fp = fopen (filename, "w+");
	    fwrite(buffer, 1, IMAGE_SIZE, fp);
    }
    printf("time: %lld", (get_current_time_with_ms() - starttime));
    fclose(fp);

    // closing the connected socket
	cam_close(client_fd);
    return 0;
}
