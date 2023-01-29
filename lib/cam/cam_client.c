// Client side C/C++ program to demonstrate Socket
// programming
#include <arpa/inet.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#define PORT 12351

#define IMAGE_SIZE 640*480*3 //160×120x3
 
int main(int argc, char const* argv[])
{
    int sock = 0, valread, client_fd;
    struct sockaddr_in serv_addr;
    char* hello = "Hello from client";
    char buffer[IMAGE_SIZE] = { 0 };
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("\n Socket creation error \n");
        return -1;
    }
 
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
 
    // Convert IPv4 and IPv6 addresses from text to binary
    // form
    if (inet_pton(AF_INET, "130.229.159.97", &serv_addr.sin_addr)
        <= 0) {
        printf(
            "\nInvalid address/ Address not supported \n");
        return -1;
    }
 
    if ((client_fd
         = connect(sock, (struct sockaddr*)&serv_addr,
                   sizeof(serv_addr)))
        < 0) {
        printf("\nConnection Failed \n");
        return -1;
    }
    //send(sock, hello, strlen(hello), 0);
    //printf("Hello message sent\n");

    int res = 0;
    int bytes_read = 0;
    while (bytes_read < IMAGE_SIZE && res != -1) {
        res = read(sock, buffer + bytes_read, IMAGE_SIZE - bytes_read);
        if (res < 1) {
            break;
        }
        bytes_read += res;
        printf("bytes_read %d\n", bytes_read);
    }

	FILE* fp = fopen ("file1.png", "w+");
    //printf("%c\n", buffer[3]);
	fwrite(buffer, 1, IMAGE_SIZE, fp);
    // closing the connected socket
    fclose(fp);
	close(client_fd);
    return 0;
}
