#ifndef _STREAM_USB_VECTOR_H_
#define _STREAM_USB_VECTOR_H_

#include <iostream>
#include <ctime>
#include <fstream>
#include <string>
#include <array>
#include <bitset>


#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include "bulkloopapp.h"

using namespace std;

//handle of selected device to work on
extern libusb_device *device;
extern libusb_device_handle *dev_handle;
extern struct libusb_device_descriptor desc_main;


//extern array<char, 1754060> buffer;
//extern array<char, 1024> buffer;
//extern array<char, 1350000> buffer; VGA
//extern array<char, 10800000> buffer;
//extern array<char, 21600000> buffer;//work
//extern array<unsigned char, 1024> buffer;
//
extern pthread_mutex_t transfer_lock;
extern pthread_cond_t transfer_cond;
extern pthread_mutex_t prepare_lock;
extern pthread_cond_t prepare_cond;
extern pthread_mutex_t cap_lock;
extern pthread_cond_t cap_cond;
extern pthread_mutex_t process_lock;
extern pthread_cond_t process_cond;
extern unsigned char buffer[1024 * 16];
extern unsigned char transfer_buffer[1024 * 16];
extern bool transfer_buffer_prepared;
extern bool cap_buffer_prepared;

 
extern unsigned char glInEpNum;
extern unsigned char glOutEpNum;
extern unsigned int  glInMaxPacketSize;
extern unsigned int  glOutMaxPacketSize;

void  device_info();

int get_ep_info(void);

void  bulk_transfer();

int print_info(libusb_device **devs);

void show_help();

void scan_arg();

int power(int c, int d);

void  custom_transfer();

void  out_transfer();

void  in_transfer();

void printf_binary(unsigned char n);

void fprintf_binary(FILE *f, unsigned char n);

void  GPIO_init();

void  *GPIO_write(void *);

void  streamOUT_transfer();

void  *streamOUT_transfer_parallel(void *);

void  streamIN_transfer();


#endif

