/* 
* bulkloopapp.c -- Program for testing USB communication using libusb 1.0
* Cypress semiconductor. 2011
* modified by Sungil Kim
*/

#include <iostream>
#include <ctime>
#include <fstream>
#include <string>

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
//#include "bulkloopapp.h"
#include <libusb-1.0/libusb.h>
#include <bitset>
#include <istream>
#include <sstream>
#include <vector>

#include "opencv/cv.h"
#include "opencv2/video/tracking.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include "opencv2/highgui/highgui.hpp"
#include "opencv2/core/core.hpp"
#include "colormap.hpp"

using namespace std;
using namespace cv;

//handle of selected device to work on
libusb_device *device;
libusb_device_handle *dev_handle;

unsigned char glInEpNum=0;
unsigned char glOutEpNum=0;
unsigned int  glInMaxPacketSize=0;
unsigned int  glOutMaxPacketSize=0;

void save_image(const string filename, const Mat& src, int colormap) {
    Mat cm_dst;
    applyColorMap(src, cm_dst, colormap);
    cm_dst.convertTo(cm_dst, CV_8UC3, 255.0);
    imwrite(filename, cm_dst);
}

void  device_info()
{
    struct libusb_config_descriptor *config;
    const struct libusb_interface *inter;
    const struct libusb_interface_descriptor *interdesc;
    const struct libusb_endpoint_descriptor *epdesc;
    int i,j,k;

    i = j = k = 0;
    libusb_get_config_descriptor(device, 0, &config);
    printf("\n\n");
    printf("----------------------------------------------------------------------------------------");
    printf("\nNumber of interfaces %15d",(int) config->bNumInterfaces);

    for(i=0;i<(int)config->bNumInterfaces;i++)
    {
        inter = &config->interface[i];
        printf("\nNumber of alternate settings %7d",inter->num_altsetting);
        printf("\n");
        for(j=0;j<inter->num_altsetting;j++)
        {
            interdesc = &inter->altsetting[j];
            printf("\ninterface Number %d, Alternate Setting %d,Number of Endpoints %d\n",\
                    (int)interdesc->bInterfaceNumber,(int) interdesc->bAlternateSetting,(int) interdesc->bNumEndpoints);
            for(k=0;k<(int) interdesc->bNumEndpoints;k++)
            {
                epdesc = &interdesc->endpoint[k];
                printf("\nEP Address %5x\t",(int) epdesc->bEndpointAddress);
                switch((epdesc->bmAttributes)&0x03)
                {
                    case 0:
                        printf("BULK IN Endpoint");
                        break;
                    case 1:
                        if((epdesc->bEndpointAddress) & 0x80)
                            printf("Isochronous IN Endpoint");
                        else
                            printf("Isochronous OUT Endpoint");
                        break;
                    case 2:
                        if((epdesc->bEndpointAddress) & 0x80)
                            printf("Bulk IN Endpoint");
                        else
                            printf("Bulk OUT Endpoint");
                        break;
                    case 3:
                        if((epdesc->bEndpointAddress) & 0x80)
                            printf("Interrupt IN Endpoint");
                        else
                            printf("Interuppt OUT Endpoint");
                        break;
                }
                printf("\n");
            }
        }
    }
    printf("----------------------------------------------------------------------------------------");
    printf("\n\n");

    libusb_free_config_descriptor(config);
}

int get_ep_info(void)
{
	
	int err;	
	struct libusb_device_descriptor desc;
	struct libusb_config_descriptor *config;
    const struct libusb_interface *inter;
    const struct libusb_interface_descriptor *interdesc;
    const struct libusb_endpoint_descriptor *epdesc;
    int k;

	//detect the bulkloop is running from VID/PID 
    err = libusb_get_device_descriptor(device, &desc);
    if (err < 0) 
    {
        printf("\n\tFailed to get device descriptor for the device, returning");
        return 1;
    }

    if((desc.idVendor == 0x04b4) && (desc.idProduct == 0x00F1))
        printf("\n\nFound FX3 bulkloop device, continuing...\n");
	else if((desc.idVendor == 0x04b4) && (desc.idProduct == 0x1004))
        printf("\n\nFound FX2LP bulkloop device, continuing...\n");

    else
    {
        printf("\n ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------");  
        printf("\nFor seeing whole bulkloop action from HOST -> TARGET ->HOST, Please run correct firmware on TARGET and restart this program");
        printf("\n -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------");  
        return 1;
    }

	k = 0;
    libusb_get_config_descriptor(device, 0, &config);
	/* this device has only one interface */
	if(((int) config->bNumInterfaces)>1)
	{
		printf("to many interfaces\n");		
		return 1;
	}    

	
	/* Interface has only two bulk Endpoints */
    inter = &config->interface[0];
	interdesc = &inter->altsetting[0];
	if(((int) interdesc->bNumEndpoints)>2)
	{
		printf("to many Endpoints\n");		
		return 1;
	}    

	/*find Endpoint address, direction and size*/
	for(k=0;k<(int) interdesc->bNumEndpoints;k++)
	{

		epdesc = &interdesc->endpoint[k];
	
		if((epdesc->bEndpointAddress) & 0x80)
		{
			printf("Bulk IN Endpoint 0x%02x\n", epdesc->bEndpointAddress);
			glInEpNum=epdesc->bEndpointAddress;
			glInMaxPacketSize=epdesc->wMaxPacketSize;		
		}
		else
		{
			printf("Bulk OUT Endpoint 0x%02x\n", epdesc->bEndpointAddress);
			glOutEpNum=epdesc->bEndpointAddress;
			glOutMaxPacketSize=epdesc->wMaxPacketSize;		
		}
	} 
    
	if(glOutMaxPacketSize!=glInMaxPacketSize)
	{
		printf("\nEndpoints size is not maching\n");		
		return 1;

	}
    libusb_free_config_descriptor(config);
	return 0;


}

//Print info about the buses and devices.
int print_info(libusb_device **devs)
{	
	int i,j;
	int busNo, devNo;
    int err = 0;

    i = j = 0;
    
    printf("\nList of Buses and Devices attached :- \n\n");    
	while ((device = devs[i++]) != NULL) 
	{
		struct libusb_device_descriptor desc;

		int r = libusb_get_device_descriptor(device, &desc);
		if (r < 0) 
		{
			printf("\n\tFailed to get device descriptor for the device, returning");
			return err;
	    }

		printf("Bus: %03d Device: %03d: Device Id: %04x:%04x\n",
			libusb_get_bus_number(device),libusb_get_device_address(device),
			desc.idVendor, desc.idProduct );
	}
	printf("\nChoose the device to work on, From bus no. and device no. :-");
	printf("\nEnter the bus no : [e.g. 2]      :");
	err = scanf("%d",&busNo);
	printf("Enter the device no : [e.g. 5]  :");
	err = scanf("%d",&devNo);	
	
	while ((device = devs[j++]) != NULL) 
	{
		struct libusb_device_descriptor desc;

		libusb_get_device_descriptor(device, &desc);
	    if ( busNo == libusb_get_bus_number(device))
	    {
	        if ( devNo == libusb_get_device_address(device))
	        {
                printf("\n --------------------------------------------------------------------------------------------");  
	            printf("\nYou have selected USB device : %04x:%04x:%04x\n\n", \
	            desc.idVendor, desc.idProduct,desc.bcdUSB);
	            return 0;
	         }
	    }
	}    

    printf("\nIllegal/nonexistant device, please restart and enter correct busNo, devNo");
    return err;
}

// Show command line help
void show_help()
{
	// Show the help to user with all the valid argument format	
	//printf("\n\t USBTestApp -- HELP \n\n");
	return;
}

// scan the arguments givan by user
void scan_arg()
{
	//If arguments not correct show help
	show_help();	
	return;
}

int power(int c, int d)
{
    int pow=1;
    int i=1;
    while(i<=d) 
    {
        pow=pow*c;
        i++;
    }
    return pow;
}

void printf_binary(unsigned char n) {
    int bin_num[8];
    int i = 0;
    int index = 0;
    for(i = 0; i < 8; i++) {
        bin_num[i] = 0;
    }
    while (n) {
        if (n & 1)
            bin_num[index] = 1;
        else
            bin_num[index] = 0;
        n >>= 1;
        index++;
    }
    for(i = 0; i < 8; i++) {
        printf("%d", bin_num[i]);
    }
}


void fprintf_binary(FILE *f, unsigned char n) {
    int bin_num[8];
    int i = 0;
    int index = 0;
    for(i = 0; i < 8; i++) {
        bin_num[i] = 0;
    }
    while (n) {
        if (n & 1)
            bin_num[index] = 1;
        else
            bin_num[index] = 0;
        n >>= 1;
        index++;
    }
    for(i = 7; i >= 0; i--) {
        fprintf(f, "%d", bin_num[i]);
    }
}

void  streamIN_transfer_no_file()
{
    int err;
    int i;
    int usr_choice,data_byte;
    int transffered_bytes; //actual transffered bytes
    unsigned char in_data_buf[1024 * 16];
    //unsigned char in_data_buf[512];
    unsigned char in_row_buf[4];
    int index;
    struct libusb_device_descriptor desc;
    unsigned char enum_glInEpNum=0;

    //ofstream ofs("streamIN_bin.txt"); // write as txt

    /*
    printf("\n-------------------------------------------------------------------------------------------------");  
    printf("\nThis function is for testing the bulk transfers. It will read from IN endpoint");
    printf("\n-------------------------------------------------------------------------------------------------");      
    */

    //detect the bulkloop is running from VID/PID 
    err = libusb_get_device_descriptor(device, &desc);
    if (err < 0) 
    {
        printf("\n\tFailed to get device descriptor for the device, returning");
        return;
    }


	if(get_ep_info())
	{
		printf("\n can not get EP Info; returning");
        return;
	}

  
    // While claiming the interface, interface 0 is claimed since from our bulkloop firmware we know that. 
    err = libusb_claim_interface (dev_handle, 0);
    if(err)
    {
        printf("\nThe device interface is not getting accessed, HW/connection fault, returning");
        return;
    }

    //FILE *f = fopen("streamIN_string.txt", "wb");

    int last_addr;
    int write_frame;

    while(1) {

        //printf("\n-------------------------------------------------------------------------------------------------");  
        transffered_bytes = 0;
        //printf("\nTransfering %d bytes from TARGET(Bulkloop device) -> HOST(PC)", glInMaxPacketSize);
        //for(enum_glInEpNum = 0; enum_glInEpNum < 32; enum_glInEpNum = enum_glInEpNum+1){
        //err = libusb_bulk_transfer(dev_handle,enum_glInEpNum,in_data_buf,glInMaxPacketSize,&transffered_bytes,100);
        err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf,glInMaxPacketSize*16,&transffered_bytes,0);
        //err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf,512,&transffered_bytes,100000);
        if(err)
        {

            //printf("\nBulk IN Endpoint 0x%02x\n", glInEpNum);
            //printf("\nTransffer failed, err: %d transffred bytes : %d",err,transffered_bytes);
            //return;
        }     
    
        /*
        printf("\n\n------------------------------------------------------------------------------------------------------------------");
        printf("\n\nData Received: %d bytes\n\n", transffered_bytes);
        printf("\n\nwriting to StreamIn.txt\n\n");
        */
        
    }

     //printf("\n\n------------------------------------------------------------------------------------------------------------------\n\n");     
     //fclose(f);
     
     //release the interface claimed earlier
     err = libusb_release_interface (dev_handle, 0);     
     if(err)
     {
        printf("\nThe device interface is not getting released, if system hangs please disconnect the device, returning");
        return;
     }
}


void  streamIN_transfer_to_file()
{
    int err;
    int i;
    int usr_choice,data_byte;
    int transffered_bytes; //actual transffered bytes
    unsigned char in_data_buf[1024 * 8];
    //unsigned char in_data_buf[512];
    unsigned char in_row_buf[4];
    int index;
    struct libusb_device_descriptor desc;
    unsigned char enum_glInEpNum=0;

    ofstream ofs;
    ofs.open("streamIN_bin.txt", ios::out | ios::binary); // write as txt

    printf("\n-------------------------------------------------------------------------------------------------");  
    printf("\nThis function is for testing the bulk transfers. It will read from IN endpoint");
    printf("\n-------------------------------------------------------------------------------------------------");      

    //detect the bulkloop is running from VID/PID 
    err = libusb_get_device_descriptor(device, &desc);
    if (err < 0) 
    {
        printf("\n\tFailed to get device descriptor for the device, returning");
        return;
    }


	if(get_ep_info())
	{
		printf("\n can not get EP Info; returning");
        return;
	}

  
    // While claiming the interface, interface 0 is claimed since from our bulkloop firmware we know that. 
    err = libusb_claim_interface (dev_handle, 0);
    if(err)
    {
        printf("\nThe device interface is not getting accessed, HW/connection fault, returning");
        return;
    }

    //FILE *f = fopen("streamIN_binary.txt", "wb");

    int last_addr;
    int write_frame;

    while(1) {

        //printf("\n-------------------------------------------------------------------------------------------------");  
        transffered_bytes = 0;
        //printf("\nTransfering %d bytes from TARGET(Bulkloop device) -> HOST(PC)", glInMaxPacketSize);
        //for(enum_glInEpNum = 0; enum_glInEpNum < 32; enum_glInEpNum = enum_glInEpNum+1){
        //err = libusb_bulk_transfer(dev_handle,enum_glInEpNum,in_data_buf,glInMaxPacketSize,&transffered_bytes,100);
        err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf,glInMaxPacketSize*8,&transffered_bytes,0);
        //err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf,512,&transffered_bytes,100000);
        if(err)
        {

            //printf("\nBulk IN Endpoint 0x%02x\n", glInEpNum);
            //printf("\nTransffer failed, err: %d transffred bytes : %d",err,transffered_bytes);
            //return;
        }     
    
        /*
        printf("\n\n------------------------------------------------------------------------------------------------------------------");
        printf("\n\nData Received: %d bytes\n\n", transffered_bytes);
        printf("\n\nwriting to StreamIn.txt\n\n");
        */
        
        
        for(i=0; i < (int)transffered_bytes; i++){

            //printf("transferred number of bytes: %d\n", transffered_bytes);
            //fprintf(f, "%d\t", in_data_buf[i]);
            index = i%4;
            in_row_buf[3 - index] = in_data_buf[i]; 
            //fprintf_binary(f, in_data_buf[i]);

            if(index == 3) {
                uint32_t data =  (uint32_t)in_data_buf[i] << 24 & 0xFF000000| 
                        (uint32_t)in_data_buf[i-1] << 16 & 0x00FF0000| 
                        (uint32_t)in_data_buf[i-2] << 8 & 0x0000FF00| 
                        (uint32_t)in_data_buf[i-3] & 0x000000FF;
                bitset<32> data_bin(data);
                
                int header = (data & 0xFE000000) >> 25;
                int addr = (data & 0x01FFE000) >> 13;

                if(last_addr > 2490 && addr > 50 && addr < last_addr) {
                    write_frame = 1;
                    last_addr = 0;
                        //ofs << "addr: " << addr << endl;
                        //ofs << "last_addr: " << last_addr << endl;
                } else if(last_addr > 2490 && addr > 5 && addr < last_addr && addr < 50) {
                    write_frame = 0;
                    last_addr = 0;
                        //ofs << "addr: " << addr << endl;
                        //ofs << "last_addr: " << last_addr << endl;
                }
                if (write_frame) {
                //if (write_frame) {
                //if (ofs) {
                    // easy way, use the stream insertion operator
                    //ofs << data_bin << endl;
                    ofs.write((char*)&data, sizeof(uint32_t));
		    //fwrite(data, 1, sizeof(unsigned long), f);
                    //	ofs << header << endl;
                    //	ofs << addr << endl;
                    //	ofs << write_frame << endl;
                }
		last_addr = addr;
	    }

	    /*
            if(index == 3) {
                
                fprintf_binary(f, in_data_buf[i]);
                fprintf_binary(f, in_data_buf[i-1]);
                fprintf_binary(f, in_data_buf[i-2]);
                fprintf_binary(f, in_data_buf[i-3]);
                fprintf(f, "\n");

            }
	    */

        }
    }

     //printf("\n\n------------------------------------------------------------------------------------------------------------------\n\n");     
     //fclose(f);
     ofs.close();

     //release the interface claimed earlier
     err = libusb_release_interface (dev_handle, 0);     
     if(err)
     {
        printf("\nThe device interface is not getting released, if system hangs please disconnect the device, returning");
        return;
     }
}


void  streamIN_transfer_to_display()
{
    int err;
    int i;
    int usr_choice,data_byte;
    int transffered_bytes; //actual transffered bytes
    unsigned char in_data_buf[1024 * 8];
    //unsigned char in_data_buf[512];
    unsigned char in_row_buf[4];
    int index;
    struct libusb_device_descriptor desc;
    unsigned char enum_glInEpNum=0;

    //ofstream ofs;
    //ofs.open("streamIN_bin.txt", ios::out | ios::binary); // write as txt
 
    const int subimg_rows = 50;
    const int subimg_cols = 50;
    const int overlap = 8;
    const int maxdisp = 128;
    int frameCounter = 0;
    char frameCounter_string[1024];
    char result_file_string[1024];
    int rowCounter = 0;
    int colCounter = 0;
    int row_shift = 0;
    int col_shift = 0;
    int image_num = 2;
    int max_col = 18;//14
    int row_num = 480;//433
    int col_num = 752;//589
 
    int Min = 255;

    int tmp = 0;
    int MAX_VALUE = 230000;
    int line_cnt = 0;

    //namedWindow("Display window", WINDOW_AUTOSIZE);
    Mat dispMap = Mat::zeros(image_num * row_num, col_num, DataType<uint8_t>::type);
    Mat dispMap_medianfilter = Mat::zeros(image_num * row_num, col_num, DataType<uint8_t>::type);
    int addr = 0;
    int last_addr = 0;
    int disp;
    int sub_row = 0;
    int sub_col = 0;
    string addr_bin;
    string disp_bin;
    string conf_bin;

    for ( int row = 0; row < dispMap.rows; row++) {
        for (int col = 0; col < dispMap.cols; col++) {
            dispMap.at<uint8_t>(row, col) = (uint8_t)127;
        }
    }

    printf("\n-------------------------------------------------------------------------------------------------");  
    printf("\nThis function is for testing the bulk transfers. It will read from IN endpoint");
    printf("\n-------------------------------------------------------------------------------------------------");      

    //detect the bulkloop is running from VID/PID 
    err = libusb_get_device_descriptor(device, &desc);
    if (err < 0) 
    {
        printf("\n\tFailed to get device descriptor for the device, returning");
        return;
    }


	if(get_ep_info())
	{
		printf("\n can not get EP Info; returning");
        return;
	}

  
    // While claiming the interface, interface 0 is claimed since from our bulkloop firmware we know that. 
    err = libusb_claim_interface (dev_handle, 0);
    if(err)
    {
        printf("\nThe device interface is not getting accessed, HW/connection fault, returning");
        return;
    }

    //FILE *f = fopen("streamIN_binary.txt", "wb");

    int write_frame;

    while(1) {

        //printf("\n-------------------------------------------------------------------------------------------------");  
        transffered_bytes = 0;
        //printf("\nTransfering %d bytes from TARGET(Bulkloop device) -> HOST(PC)", glInMaxPacketSize);
        //for(enum_glInEpNum = 0; enum_glInEpNum < 32; enum_glInEpNum = enum_glInEpNum+1){
        //err = libusb_bulk_transfer(dev_handle,enum_glInEpNum,in_data_buf,glInMaxPacketSize,&transffered_bytes,100);
        err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf,glInMaxPacketSize*8,&transffered_bytes,0);
        //err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf,512,&transffered_bytes,100000);
        if(err)
        {

            //printf("\nBulk IN Endpoint 0x%02x\n", glInEpNum);
            //printf("\nTransffer failed, err: %d transffred bytes : %d",err,transffered_bytes);
            //return;
        }     
    
        /*
        printf("\n\n------------------------------------------------------------------------------------------------------------------");
        printf("\n\nData Received: %d bytes\n\n", transffered_bytes);
        printf("\n\nwriting to StreamIn.txt\n\n");
        */
        
        
        for(i=0; i < (int)transffered_bytes; i++){

            //printf("transferred number of bytes: %d\n", transffered_bytes);
            //fprintf(f, "%d\t", in_data_buf[i]);
            index = i%4;
            in_row_buf[3 - index] = in_data_buf[i]; 
            //fprintf_binary(f, in_data_buf[i]);

            if(index == 3) {
                uint32_t data =  (uint32_t)in_data_buf[i] << 24 & 0xFF000000| 
                        (uint32_t)in_data_buf[i-1] << 16 & 0x00FF0000| 
                        (uint32_t)in_data_buf[i-2] << 8 & 0x0000FF00| 
                        (uint32_t)in_data_buf[i-3] & 0x000000FF;
                bitset<32> data_bin(data);
                
                int header = (data & 0xFE000000) >> 25;
                int addr = (data & 0x01FFE000) >> 13;
                int disp = (data & 0x00000FFF) >> 5;

                //cout << data_bin.to_string() << endl;;
                //cout << disp << endl;

                if(last_addr > 2490 && addr > 50 && addr < last_addr) {
                    write_frame = 1;
                    //last_addr = 0;
                        //cout << "addr: " << addr << endl;
                        //cout << "last_addr: " << last_addr << endl;
                } else if(last_addr > 2490 && addr > 5 && addr < last_addr && addr < 50) {
                    write_frame = 0;
                    //last_addr = 0;
                        //cout << "addr: " << addr << endl;
                        //cout << "last_addr: " << last_addr << endl;
                }
                if (write_frame) {
                    //write a binary file
                    //ofs.write((char*)&data, sizeof(uint32_t));
                    //
                    //cout << "header: " << header << endl;
                    if (header == 117) { // 110101
                        //last frame is done
                        if(last_addr > 2490 && addr > 50 && addr < last_addr) {
                            //cout << "display" << endl;
                            //imshow("depth", dispMap);
                            Mat dispMap_left(dispMap, Range(0, row_num), Range::all());
                            Mat dispMap_right_flip(dispMap, Range(row_num, 2*row_num), Range::all());
                            Mat dispMap_right;
                            flip(dispMap_right_flip, dispMap_right, 1);
                            Mat dispMap_LRcheck = Mat::zeros(row_num, col_num, DataType<uint8_t>::type);
                            Mat dispMap_left_copied = dispMap_left.clone();
                            Mat dispMap_right_copied = dispMap_right.clone();
                            Mat consistency = Mat::zeros(row_num, col_num, DataType<uint8_t>::type);

                            //LR check
                            int LR_threshold = 4;
                            for(int row = 0; row < row_num; row++){
                                for(int col = 0; col < col_num; col++){
                                    if(col - dispMap_left_copied.at<uint8_t>(row, col) < col_num && col - dispMap_left_copied.at<uint8_t>(row, col) >= 0){
                                        consistency.at<uint8_t>(row, col) = (uint8_t)abs((dispMap_right_copied.at<uint8_t>(row,col - (int)dispMap_left_copied.at<uint8_t>(row,col)) - dispMap_left_copied.at<uint8_t>(row,col)));
                                    }
                                    else{
                                        consistency.at<uint8_t>(row, col) = 255;
                                    }
                                    if(consistency.at<uint8_t>(row, col) < LR_threshold){
                                        dispMap_LRcheck.at<uint8_t>(row, col) = dispMap.at<uint8_t>(row, col);
                                    }
                                    else{
                                        dispMap_LRcheck.at<uint8_t>(row, col) = 255;
                                    }
                                }
                            }
                            Mat dispMap_LR_check_color;
                            Mat dispMap_LR_check_scaled = Mat::zeros(dispMap_LRcheck.rows, dispMap_LRcheck.cols, DataType<uint8_t>::type);
                            Mat dispMap_color = Mat::zeros(2 * dispMap.rows, dispMap.cols, DataType<uint8_t>::type);
                         
                            Min = 255;
                            tmp = 0;
                            MAX_VALUE = 230000;
                            for(int row = 0; row < dispMap_LRcheck.rows; row++){
                                for(int col = 0; col < dispMap_LRcheck.cols; col++){

                                    if(dispMap_LRcheck.at<uint8_t>(row, col) != 0) {
                                        tmp = dispMap_LRcheck.at<uint8_t>(row, col);
                                    } else {
                                        tmp = 1;
                                    }
                                    if(tmp < Min && tmp != 0){
                                        Min = tmp;
                                    }

                                    //tmp = (int) 16 * (tmp - Min);
                                    tmp = (int) 8 * tmp;

                                    if(0 < dispMap_LRcheck.at<uint8_t>(row, col) && dispMap_LRcheck.at<uint8_t>(row, col) < 255) { 
                                        if(tmp < 255) {
                                            dispMap_LR_check_scaled.at<uint8_t>(row, col) = (uint8_t) 255 - tmp ;
                                        } else {
                                            dispMap_LR_check_scaled.at<uint8_t>(row, col) = (uint8_t) 255 - 254 ;
                                        }
                                    } else if(dispMap_LRcheck.at<uint8_t>(row, col) == 255){
                                        dispMap_LR_check_scaled.at<uint8_t>(row, col) = 255;
                                        //img_new.at<uint8_t>(row, col) = 1;
                                    } else if(dispMap_LRcheck.at<uint8_t>(row, col) == 0){
                                        dispMap_LR_check_scaled.at<uint8_t>(row, col) = 255;
                                    } else {
                                        dispMap_LR_check_scaled.at<uint8_t>(row, col) = 255;
                                    }
                                }
                            }
                            /*
                            //clean disp map
                            for ( int row = 0; row < dispMap.rows; row++) {
                                for (int col = 0; col < dispMap.cols; col++) {
                                    dispMap.at<uint8_t>(row, col) = (uint8_t)127;
                                }
                            }
                            */

                            //cout << (int)Min << std::endl;

                            //dispMap_medianfilter = median_filter(dispMap_LR_check_scaled, 3);
                            medianBlur(dispMap_LR_check_scaled, dispMap_medianfilter, 5);
                            applyColorMap(dispMap_medianfilter, dispMap_LR_check_color, COLORMAP_RAINBOW);
                            dispMap_LR_check_color.convertTo(dispMap_LR_check_color, CV_8UC3, 255.0);
                            //save_image(dispMap_LR_check_color_string, dispMap_LR_check_color, COLORMAP_RAINBOW);
                            //imwrite(dispMap_LR_check_color_string, dispMap_LR_check_color);

                            imshow("depth", dispMap_LR_check_color);
                            waitKey(1);

                            sub_row = 0;
                            sub_col = 0;
                            rowCounter = 0;
                            colCounter = 0;
                            row_shift = 0;
                            col_shift = 0;
                            last_addr = 0;

                            dispMap_left.release();
                            dispMap_right.release();                    
                            consistency.release();
                            dispMap_LRcheck.release();
                            dispMap_LR_check_scaled.release();

                        }

                        col_shift = colCounter * (50 - overlap);
                        row_shift = rowCounter * (50 - overlap);
                        sub_row = int(addr/50);
                        sub_col = int(addr%50);
                        if( sub_col < (50 - overlap/2) && 
                            sub_row < (50 - overlap/2) &&
                            sub_col >= (overlap/2) &&
                            sub_row >= (overlap/2) &&
                            sub_row + row_shift < image_num * row_num && 
                            sub_col + col_shift < col_num){

                            dispMap.at<uint8_t>(sub_row + row_shift, sub_col + col_shift) = uint8_t(disp);
                        }
                        if (addr < last_addr && last_addr > 2490) {
                            colCounter++;
                            if(colCounter == max_col) {
                                rowCounter++;
                                colCounter = 0;
                            }
                        }
                    }
                }
                last_addr = addr;
            }
        }
    }

     //printf("\n\n------------------------------------------------------------------------------------------------------------------\n\n");     
     //fclose(f);
     //ofs.close();

     //release the interface claimed earlier
     err = libusb_release_interface (dev_handle, 0);     
     if(err)
     {
        printf("\nThe device interface is not getting released, if system hangs please disconnect the device, returning");
        return;
     }
}

/*
void process_buffer(unsigned char *in_data_buf, int transffered_bytes){

    uint32_t head;
    uint32_t addr;
    uint32_t disp;
    uint32_t conf;
    int addr_int;
    int row_addr;
    int col_addr;
    int last_addr_int;
    int row_shift = 0;
    int col_shift = 0;
    int rowCounter = 0;
    int colCounter = 0;
    int max_col = 43;
    int max_row = 25;
    int frameCounter = 0;
    char frame_string[1024];

    while(1) { //runs a loop, never finish

        //only process if mutex is locked

        //iterate over all 1024 bytes
        for(int i=0; i < (int)transffered_bytes; i++){
            //printf("%d\t",in_data_buf[i]);
            //fprintf(f, "%d\t", in_data_buf[i]);
            index = i%4;
            //in_row_buf[3 - index] = in_data_buf[i]; 
            //fprintf_binary(f, in_data_buf[i]);

            if(index == 3) {
                data =  (uint32_t)in_data_buf[i] << 24 & 0xFF000000| 
                        (uint32_t)in_data_buf[i-1] << 16 & 0x00FF0000| 
                        (uint32_t)in_data_buf[i-2] << 8 & 0x0000FF00| 
                        (uint32_t)in_data_buf[i-3] & 0x000000FF;
                fprintf(data, "\n");
                //fprintf_binary(f, in_data_buf[i]);
                //fprintf_binary(f, in_data_buf[i-1]);
                //fprintf_binary(f, in_data_buf[i-2]);
                //fprintf_binary(f, in_data_buf[i-3]);
                //fprintf(f, "\n");
                head = data & 0xFC000000;
                addr = data & 0x00FFF000;
                disp = data & 0x00000FF0;//8
                conf = data & 0x00000007;
                fprintf(head, "\n");
                fprintf(addr, "\n");
                fprintf(disp, "\n");
                fprintf(conf, "\n");

                //construct_image
                col_shift = colCounter * (50 - overlap);
                row_shift = rowCounter * (50 - overlap);
                if (head == 0xD4000000){
                    addr_int = int(addr >> 12);
                    row_addr = addr_int/50;
                    col_addr = addr_int%50;
                    if( col_addr < (50 - overlap/2) && 
                        row_addr < (50 - overlap/2) &&
                        col_addr >= (overlap/2) &&
                        row_addr >= (overlap/2) &&
                        row_addr + row_shift < image_num * Ground_truth.rows && 
                        col_addr + col_shift < Ground_truth.cols){

                        
                        dispMap.at<uint8_t>(row_addr + row_shift, col_addr + col_shift) = uint8_t(disp_result >> 4);

                        if (addr - last_addr == 2) {
                            dispMap.at<uint8_t>(row_addr + row_shift, col_addr + col_shift - 1) = uint8_t(disp_result >> 4);
                        }
                    }

                    if(addr < last_addr && last_addr > 2495) {
                        colCounter++;
                        if(colCounter == max_col) {
                            rowCounter++;
                            colCounter = 0;
                            if(rowCounter == max_row) {
                                frameCounter++;
                                frame_string = sprintf("%d.png", frameCounter);
                                imwrite(dispMap, frame_string);
                                rowCounter = 0;
                                colCounter = 0;
                            }
                        }
                    }
                    last_addr = addr;
                }
            }
        }

        //unlock the lock, can stream
        
    }
}
*/

/*
void  streamIN_construct_transfer_parallel()
{
    int err;
    int i;
    int usr_choice,data_byte;
    int transffered_bytes_ping; //actual transffered bytes
    int transffered_bytes_pong; //actual transffered bytes
    unsigned char in_data_buf_ping[1024];
    unsigned char in_data_buf_pong[1024];
    //unsigned char in_data_buf[512];
    unsigned char in_row_buf[4];
    int index;
    struct libusb_device_descriptor desc;
    unsigned char enum_glInEpNum=0;
    ping_lock = PTHREAD_MUTEX_INITIALIZER;
    pong_lock = PTHREAD_MUTEX_INITIALIZER;
	

    printf("\n-------------------------------------------------------------------------------------------------");  
    printf("\nThis function is for testing the bulk transfers. It will read from IN endpoint");
    printf("\n-------------------------------------------------------------------------------------------------");      

    //detect the bulkloop is running from VID/PID 
    err = libusb_get_device_descriptor(device, &desc);
    if (err < 0) 
    {
        printf("\n\tFailed to get device descriptor for the device, returning");
        return;
    }


	if(get_ep_info())
	{
		printf("\n can not get EP Info; returning");
        return;
	}

  
    // While claiming the interface, interface 0 is claimed since from our bulkloop firmware we know that. 
    err = libusb_claim_interface (dev_handle, 0);
    if(err)
    {
        printf("\nThe device interface is not getting accessed, HW/connection fault, returning");
        return;
    }

    FILE *f = fopen("streamIN.txt", "wb");

    uint32_t data;

    process_buffer(in_data_buf_ping, transffered_bytes_ping);

    while(1) {

        //printf("\n-------------------------------------------------------------------------------------------------");  
        transffered_bytes = 0;
        //printf("\nTransfering %d bytes from TARGET(Bulkloop device) -> HOST(PC)", glInMaxPacketSize);
        //for(enum_glInEpNum = 0; enum_glInEpNum < 32; enum_glInEpNum = enum_glInEpNum+1){
        //err = libusb_bulk_transfer(dev_handle,enum_glInEpNum,in_data_buf,glInMaxPacketSize,&transffered_bytes,100);
        if(ping is unlocked & pong is locked) {
            err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf_ping,glInMaxPacketSize,&transffered_bytes_ping,1000);
            if(transffered_bytes_ping == 1024){
                lock_ping;
            }
        } else if (pong is unlocked & ping is locked) {
            err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf_ping,glInMaxPacketSize,&transffered_bytes_ping,1000);
            if(transffered_bytes_pong == 1024){
                lock_pong;
            }
        }

        //err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf,512,&transffered_bytes,100000);
        //if(err)
        //{

            //printf("\nBulk IN Endpoint 0x%02x\n", glInEpNum);
            //printf("\nTransffer failed, err: %d transffred bytes : %d",err,transffered_bytes);
            //return;
        //}     
    
     //}
        //printf("\n\n------------------------------------------------------------------------------------------------------------------");
        //printf("\n\nData Received: %d bytes\n\n", transffered_bytes);
        //printf("\n\nwriting to StreamIn.txt\n\n");

        

    }

     //printf("\n\n------------------------------------------------------------------------------------------------------------------\n\n");     
     fclose(f);
     
     //release the interface claimed earlier
     err = libusb_release_interface (dev_handle, 0);     
     if(err)
     {
        printf("\nThe device interface is not getting released, if system hangs please disconnect the device, returning");
        return;
     }
}
*/



/*
void  streamIN_construct_transfer()
{
    int err;
    int i;
    int usr_choice,data_byte;
    int transffered_bytes_ping; //actual transffered bytes
    int transffered_bytes_pong; //actual transffered bytes
    unsigned char in_data_buf_ping[1024];
    unsigned char in_data_buf_pong[1024];
    //unsigned char in_data_buf[512];
    unsigned char in_row_buf[4];
    int index;
    struct libusb_device_descriptor desc;
    unsigned char enum_glInEpNum=0;
    ping_lock = PTHREAD_MUTEX_INITIALIZER;
    pong_lock = PTHREAD_MUTEX_INITIALIZER;
	

    printf("\n-------------------------------------------------------------------------------------------------");  
    printf("\nThis function is for testing the bulk transfers. It will read from IN endpoint");
    printf("\n-------------------------------------------------------------------------------------------------");      

    //detect the bulkloop is running from VID/PID 
    err = libusb_get_device_descriptor(device, &desc);
    if (err < 0) 
    {
        printf("\n\tFailed to get device descriptor for the device, returning");
        return;
    }


	if(get_ep_info())
	{
		printf("\n can not get EP Info; returning");
        return;
	}

  
    // While claiming the interface, interface 0 is claimed since from our bulkloop firmware we know that. 
    err = libusb_claim_interface (dev_handle, 0);
    if(err)
    {
        printf("\nThe device interface is not getting accessed, HW/connection fault, returning");
        return;
    }

    FILE *f = fopen("streamIN.txt", "wb");

    uint32_t data;

    while(1) {

        //printf("\n-------------------------------------------------------------------------------------------------");  
        transffered_bytes = 0;
        //printf("\nTransfering %d bytes from TARGET(Bulkloop device) -> HOST(PC)", glInMaxPacketSize);
        //for(enum_glInEpNum = 0; enum_glInEpNum < 32; enum_glInEpNum = enum_glInEpNum+1){
        //err = libusb_bulk_transfer(dev_handle,enum_glInEpNum,in_data_buf,glInMaxPacketSize,&transffered_bytes,100);
        if(pong is locked) {
            err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf_ping,glInMaxPacketSize,&transffered_bytes_ping,1000);
        } else if (ping is locked) {
            err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf_ping,glInMaxPacketSize,&transffered_bytes_ping,1000);
        }

        //err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf,512,&transffered_bytes,100000);
        //if(err)
        //{

            //printf("\nBulk IN Endpoint 0x%02x\n", glInEpNum);
            //printf("\nTransffer failed, err: %d transffred bytes : %d",err,transffered_bytes);
            //return;
        //}     
    
     //}
        
        //printf("\n\n------------------------------------------------------------------------------------------------------------------");
        //printf("\n\nData Received: %d bytes\n\n", transffered_bytes);
        //printf("\n\nwriting to StreamIn.txt\n\n");
        
        process_buffer(in_data_buf_ping, transffered_bytes_ping);
        

    }

     //printf("\n\n------------------------------------------------------------------------------------------------------------------\n\n");     
     fclose(f);
     
     //release the interface claimed earlier
     err = libusb_release_interface (dev_handle, 0);     
     if(err)
     {
        printf("\nThe device interface is not getting released, if system hangs please disconnect the device, returning");
        return;
     }
}
*/

int main()
{
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
    
    do{
        //what user want to do with selected device
        printf("What do you want to do ?");
        printf("\n1. Give information about the device.");
        printf("\n2. Do the streawm IN to file");
        printf("\n3. Do the streawm IN without writing file");
        printf("\n4. Do the streawm IN with display");
        printf("\n5. Exit");
        printf("\n\nEnter the choice [e.g 3]   :");
        err = scanf("%d",&usr_choice);
       
        switch(usr_choice)
        {
            case 1: //displays end points (EP)
                device_info();
                break;
			case 2:
					streamIN_transfer_to_file(); 
					return 0;
			case 3:
					streamIN_transfer_no_file(); 
					return 0;
			case 4:
					streamIN_transfer_to_display(); 
                    return 0;
			case 5:
					printf("\nExiting");
					return 0;                
			default:
					printf("\nPlease enter the correct choice between 1 to 8\n");
			}
    }while(1); // loop continuously till exit
             
    //All tasks done close the device handle
    libusb_close(dev_handle);
    
    //Exit from libusb library
    libusb_exit(NULL);
    
    return 0;
}
