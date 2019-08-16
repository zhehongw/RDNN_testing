#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <stdio.h>
#include <cmath>
#include <string>
#include <bitset>
#include <string.h>
#include <cstring>
#include <ctime>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>
#include "bulkloopapp.h"
#include "stream_usb_vector.h"
#include "opencv/cv.h"
#include "opencv2/video/tracking.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include "opencv2/highgui/highgui.hpp"
#include "opencv2/core/core.hpp"
#include "opencv2/calib3d/calib3d.hpp"

#include <opencv2/opencv.hpp>
#include <pthread.h>

using namespace std;
using namespace cv;

int _count;

Mat left_read, right_read;

string HexToBin(string s){
    const int num_of_bits = 12;
    stringstream ss;
    ss << hex << s;
    unsigned n;
    ss >> n;
    return bitset<num_of_bits>(n).to_string();
}

int main () {
    pthread_t threads_0;
    int iret[1];

    //streaming out
    int err;
    int usr_choice;
    ssize_t cnt;  // USB device count
    libusb_device **devs; //USB devices
    //scan the arguments amd make sence out of them
    scan_arg();

    //initialise the libusb library
    err = libusb_init(NULL);
    if(err)
    {
        printf("\n\t The libusb library failed to initialise, returning");
        return(err);
     }   

    //Detect all devices on the USB bus.
    cnt = libusb_get_device_list(NULL, &devs);
    if (cnt < 0)
    {
        printf("\n\t No device is connected to USB bus, returning ");
        return (int)cnt;
    }
    
    //print all devices on the bus 
    err = print_info(devs);
    if(err)
    {
        printf("\nEnding the program, due to error\n");
        return(err);
    }   
    
    //open the device handle for all future operations
    err = libusb_open (device, &dev_handle);
    if(err)
    {
        printf("\nThe device is not opening, check the error code, returning\n");
        return err;
    }
    
    //since the use of device list is over, free it
    libusb_free_device_list(devs, 1);

	if(get_ep_info())
	{
		printf("\n can not get EP Info; returning");
        return 0;
	}
  
    // While claiming the interface, interface 0 is claimed since from our bulkloop firmware we know that. 
    err = libusb_claim_interface (dev_handle, 0);
    if(err)
    {
        printf("\nThe device interface is not getting accessed, HW/connection fault, returning");
        return 0;
    }

    int usb_speed = libusb_get_device_speed (device);
    printf("\n current usb speed is: %d\n", usb_speed);

    //printf("\n reset chip\n");
    //reset chip
    GPIO_init();

    //printf("\n start chip\n");

    //write GPIO
    iret[0] = pthread_create(&threads_0, NULL, &GPIO_write, NULL);
    //wait until reset, afifo_reset, mux are ready
    usleep(4100000);

    //GPIO_write();

    //wait until reset, afifo_reset, debug are ready
    //usleep(3000000);

    //cout << "finishing GPIO operation" << endl;
    //transfer
    streamOUT_transfer();

    //All tasks done close the device handle
    libusb_close(dev_handle);
    
    //Exit from libusb library
    libusb_exit(NULL);
    
    return 0;
}

