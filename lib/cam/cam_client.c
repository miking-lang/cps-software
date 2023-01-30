#include <arpa/inet.h>
#include <stdio.h>
#include <unistd.h>
#include "cam_client.h"

#define PORT 12351
#define RPI_IP "130.229.159.97"

//TODO: Error handling
int cam_init(int* sock, int* client_fd) {
    struct sockaddr_in serv_addr;
    if ((*sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("\n Socket creation error \n");
        return -1;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
 
    // Convert IPv4 and IPv6 addresses from text to binary form
    if (inet_pton(AF_INET, RPI_IP, &serv_addr.sin_addr)
        <= 0) {
        printf(
            "\nInvalid address/ Address not supported \n");
        return -1;
    }
 
    if ((*client_fd
         = connect(*sock, (struct sockaddr*)&serv_addr,
                   sizeof(serv_addr)))
        < 0) {
        printf("\nConnection Failed \n");
        return -1;
    }
    return 0;
}

//TODO: Error handling
void cam_get_image(int sock, char* res) {
    uint8_t command = 1;
    send(sock, &command, 1, 0);

    int step = 0;
    int bytes_read = 0;
    while (step != -1) {
        step = read(sock, res + bytes_read, IMAGE_SIZE - bytes_read);
        if (step < 1) {
            break;
        }
        bytes_read += step;

        if (*(res + bytes_read - 7) == 'E' && *(res + bytes_read - 6) == 'N' && *(res + bytes_read - 5) == 'D') {
            break;
        }
    }
}

int cam_close(int client_fd) {
    return close(client_fd);
}