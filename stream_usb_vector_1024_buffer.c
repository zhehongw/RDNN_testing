#ifndef _STREAM_USB_VECTOR_C_
#define _STREAM_USB_VECTOR_C_

#include "stream_usb_vector.h"
#define WITH_BUFFER

using namespace std;

libusb_device *device;
libusb_device_handle *dev_handle;
struct libusb_device_descriptor main_desc;

//array<char, 1754060> buffer;
//array<char, 1350000> buffer;
//array<unsigned char, 1024> buffer;
unsigned char buffer[1024 * 16];
//unsigned char transfer_buffer[1024 * 16];
//pthread_mutex_t transfer_lock;
//pthread_cond_t transfer_cond;
//bool transfer_buffer_prepared=0;
//pthread_mutex_t prepare_lock;
//pthread_cond_t prepare_cond;

unsigned char glInEpNum=0;
unsigned char glOutEpNum=0;
unsigned int  glInMaxPacketSize=0;
unsigned int  glOutMaxPacketSize=0;

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
    {}
        //printf("\n\nFound FX3 bulkloop device, continuing...\n");
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
			//printf("Bulk IN Endpoint 0x%02x\n", epdesc->bEndpointAddress);
			glInEpNum=epdesc->bEndpointAddress;
			glInMaxPacketSize=epdesc->wMaxPacketSize;		
		}
		else
		{
			//printf("Bulk OUT Endpoint 0x%02x\n", epdesc->bEndpointAddress);
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

void  GPIO_init()
{
    int err;
    int i;
    int usr_choice,data_byte;
    struct libusb_device_descriptor desc;
    int index;
    unsigned char data[1];
    /*
    printf("\n-------------------------------------------------------------------------------------------------");  
    printf("\nThis function is for testing the bulk transfers. It will write on OUT endpoint");
    printf("\n-------------------------------------------------------------------------------------------------");      
    */
    //detect the bulkloop is running from VID/PID 
    //device_info();
    
    
    err = libusb_get_device_descriptor(device, &main_desc);
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
    

    /*
    int libusb_control_transfer     (   libusb_device_handle *      dev_handle,
                                        uint8_t     bmRequestType,
                                        uint8_t     bRequest,
                                        uint16_t    wValue,
                                        uint16_t    wIndex,
                                        unsigned char *     data,
                                        uint16_t    wLength,
                                        unsigned int    timeout 
                                        )   
    */

    printf("\nfifo reset: \n");
    data[1] = 0x01;
    //GPIO program
    //bit 7: LIBUSB_ENDPOINT_OUT
    //bit 5-6: LIBUSB_REQUEST_TYPE_VENDOR 
    //bit 0-4: LIBUSB_RECIPIENT_DEVICE
    err = libusb_control_transfer   (dev_handle,
                                    (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
                                    0xC2,
                                    0x0000,//data
                                    0x0002,//AFIFO_RESET
                                    data,
                                    1,
                                    1000 
                                    );
    #ifdef DISPLAY
    printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    #endif
    if(err < 0)
    {
        printf("\ncannot toggle GPIO because of err: %d\n", err);
        return;
    } else {
        #ifdef DISPLAY
        printf("\nGPIO written\n");
        #endif
    }

    printf("\nreset: \n");
    err = libusb_control_transfer   (dev_handle,
                                    (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
                                    0xC2,
                                    0x0000,//data
                                    0x0003,//RESET
                                    data,
                                    1,
                                    1000 
                                    );
    #ifdef DISPLAY
    printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    #endif
    if(err < 0)
    {
        printf("\ncannot toggle GPIO because of err: %d\n", err);
        return;
    } else {
        #ifdef DISPLAY
        printf("\nGPIO written\n");
        #endif
    }

    printf("\nmux reset: \n");
    err = libusb_control_transfer   (dev_handle,
                                    (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
                                    0xC2,
                                    0x0000,//data
                                    0x0004,//MUX_RESET
                                    data,
                                    1,
                                    1000 
                                    );
    #ifdef DISPLAY
    printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    #endif
    if(err < 0)
    {
        printf("\ncannot toggle GPIO because of err: %d\n", err);
        return;
    } else {
        #ifdef DISPLAY
        printf("\nGPIO written\n");
        #endif
    }

    printf("\nenable: \n");
    err = libusb_control_transfer   (dev_handle,
                                    (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
                                    0xC2,
                                    0x0000,//data
                                    0x0001,//ENABLE
                                    data,
                                    1,
                                    1000 
                                    );
    #ifdef DISPLAY
    printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    #endif
    if(err < 0)
    {
        printf("\ncannot toggle GPIO because of err: %d\n", err);
        return;
    } else {
        #ifdef DISPLAY
        printf("\nGPIO written\n");
        #endif
    }

    printf("\next clk: \n");
    err = libusb_control_transfer   (dev_handle,
                                    (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
                                    0xC2,
                                    0x0000,//data
                                    0x0000,//EXT_CLK_SEL
                                    data,
                                    1,
                                    1000 
                                    );
    #ifdef DISPLAY
    printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    #endif
    if(err < 0)
    {
        printf("\ncannot toggle GPIO because of err: %d\n", err);
        return;
    } else {
        #ifdef DISPLAY
        printf("\nGPIO written\n");
        #endif
    }

    //release the interface claimed earlier
    err = libusb_release_interface (dev_handle, 0);     
    if(err)
    {
        printf("\nThe device interface is not getting released, if system hangs please disconnect the device, returning");
        return;
    }

    printf("\nreset finish: \n");
    
    //fclose(f);
    return;
}

//void GPIO_write()
void* GPIO_write(void *)
{
    int err;
    int i;
    int usr_choice,data_byte;
    //struct libusb_device_descriptor desc;
    int index;
    unsigned char data[1];
    /*
    printf("\n-------------------------------------------------------------------------------------------------");  
    printf("\nThis function is for testing the bulk transfers. It will write on OUT endpoint");
    printf("\n-------------------------------------------------------------------------------------------------");      
    */
    //detect the bulkloop is running from VID/PID 
    //device_info();
    
    
    err = libusb_get_device_descriptor(device, &main_desc);
    if (err < 0) 
    {
        printf("\n\tFailed to get device descriptor for the device, returning");
        return NULL;
        //return;
    }

	if(get_ep_info())
	{
		printf("\n can not get EP Info; returning");
        return NULL;
        //return;
	}
  
    // While claiming the interface, interface 0 is claimed since from our bulkloop firmware we know that. 
    err = libusb_claim_interface (dev_handle, 0);
    if(err)
    {
        printf("\nThe device interface is not getting accessed, HW/connection fault, returning");
        return NULL;
        //return;
    }
    

    /*
    int libusb_control_transfer     (   libusb_device_handle *      dev_handle,
                                        uint8_t     bmRequestType,
                                        uint8_t     bRequest,
                                        uint16_t    wValue,
                                        uint16_t    wIndex,
                                        unsigned char *     data,
                                        uint16_t    wLength,
                                        unsigned int    timeout 
                                        )   
    */
    
    data[1] = 0x01;
    //GPIO program
    //bit 7: LIBUSB_ENDPOINT_OUT
    //bit 5-6: LIBUSB_REQUEST_TYPE_VENDOR 
    //bit 0-4: LIBUSB_RECIPIENT_DEVICE
    //
    //1. release clock MUX
    err = libusb_control_transfer   (dev_handle,
                                    (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
                                    0xC2,
                                    0x0001,//data
                                    0x0004,//MUX_RESET
                                    data,
                                    1,
                                    1000 
                                    );
    #ifdef DISPLAY
    printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    #endif
    if(err < 0)
    {
        printf("\ncannot toggle GPIO because of err: %d\n", err);
        return NULL;
        //return;
    } else {
        #ifdef DISPLAY
        printf("\nGPIO written\n");
        #endif
    }

    usleep(1000000);
    //2. release chip reset
    err = libusb_control_transfer   (dev_handle,
                                    (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
                                    0xC2,
                                    0x0001,//data
                                    0x0003,//RESET
                                    data,
                                    1,
                                    1000 
                                    );
    #ifdef DISPLAY
    printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    #endif
    if(err < 0)
    {
        printf("\ncannot toggle GPIO because of err: %d\n", err);
        return NULL;
        //return;
    } else {
        #ifdef DISPLAY
        printf("\nGPIO written\n");
        #endif
    }

    usleep(1000000);
    //3. release asynchronous fifo
    err = libusb_control_transfer   (dev_handle,
                                    (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
                                    0xC2,
                                    0x0001,//data
                                    0x0002,//AFIFO_RESET
                                    data,
                                    1,
                                    1000 
                                    );
    #ifdef DISPLAY
    printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    #endif
    if(err < 0)
    {
        printf("\ncannot toggle GPIO because of err: %d\n", err);
        return NULL;
        //return;
    } else {
        #ifdef DISPLAY
        printf("\nGPIO written\n");
        #endif
    }

    usleep(4000000);
    ////4. set to debug mode
    //err = libusb_control_transfer   (dev_handle,
    //                                (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
    //                                0xC2,
    //                                0x0001,//data
    //                                0x0001,//DEBUG
    //                                data,
    //                                1,
    //                                1000 
    //                                );
    //#ifdef DISPLAY
    //printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    //#endif
    //if(err < 0)
    //{
    //    printf("\ncannot toggle GPIO because of err: %d\n", err);
    //    return NULL;
    //} else {
    //    #ifdef DISPLAY
    //    printf("\nGPIO written\n");
    //    #endif
    //}

    ////delay until initialization finish
    //usleep(2000000);
    //
    ////4. release debug
    //err = libusb_control_transfer   (dev_handle,
    //                                (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
    //                                0xC2,
    //                                0x0000,//data
    //                                0x0001,//DEBUG
    //                                data,
    //                                1,
    //                                1000 
    //                                );
    //#ifdef DISPLAY
    //printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    //#endif
    //if(err < 0)
    //{
    //    printf("\ncannot toggle GPIO because of err: %d\n", err);
    //    return NULL;
    //} else {
    //    #ifdef DISPLAY
    //    printf("\nGPIO written\n");
    //    #endif
    //}

    //usleep(1000000);
    //5. select internal clk
    err = libusb_control_transfer   (dev_handle,
                                    (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
                                    0xC2,
                                    0x0001,//0001 data
                                    0x0000,//EXT_CLK_SEL
                                    data,
                                    1,
                                    1000 
                                    );
    #ifdef DISPLAY
    printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    #endif
    if(err < 0)
    {
        printf("\ncannot toggle GPIO because of err: %d\n", err);
        return NULL;
        //return;
    } else {
        #ifdef DISPLAY
        printf("\nGPIO written\n");
        #endif
    }

    usleep(100000);
    
    //release the interface claimed earlier
    err = libusb_release_interface (dev_handle, 0);     
    if(err)
    {
        printf("\nThe device interface is not getting released, if system hangs please disconnect the device, returning");
        return NULL;
        //return;
    }

    //6. select enable
    err = libusb_control_transfer   (dev_handle,
                                    (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
                                    0xC2,
                                    0x0001,//data
                                    0x0001,//ENABLE
                                    data,
                                    1,
                                    1000 
                                    );
    #ifdef DISPLAY
    printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    #endif
    if(err < 0)
    {
        printf("\ncannot toggle GPIO because of err: %d\n", err);
        return NULL;
        //return;
    } else {
        #ifdef DISPLAY
        printf("\nGPIO written\n");
        #endif
    }

    usleep(1500000);
    //2. reset chip
    err = libusb_control_transfer   (dev_handle,
                                    (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE),
                                    0xC2,
                                    0x0001,//data
                                    0x0003,//RESET
                                    data,
                                    1,
                                    1000 
                                    );
    #ifdef DISPLAY
    printf("bm: %d\n", (LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_VENDOR | LIBUSB_RECIPIENT_DEVICE));
    #endif
    if(err < 0)
    {
        printf("\ncannot toggle GPIO because of err: %d\n", err);
        return NULL;
        //return;
    } else {
        #ifdef DISPLAY
        printf("\nGPIO written\n");
        #endif
    }

    usleep(1000000);
    
    //release the interface claimed earlier
    err = libusb_release_interface (dev_handle, 0);     
    if(err)
    {
        printf("\nThe device interface is not getting released, if system hangs please disconnect the device, returning");
        return NULL;
        //return;
    }

    return NULL;
    //return ;

}

void  streamOUT_transfer()
{
    int err;
    int transffered_bytes; //actual transffered bytes
    
    printf("\n-------------------------------------------------------------------------------------------------");  
    printf("\nThis function is for testing the bulk transfers. It will write on OUT endpoint");
    printf("\n-------------------------------------------------------------------------------------------------");      
    
    //detect the bulkloop is running from VID/PID 

    //write inn main
    
    err = libusb_get_device_descriptor(device, &main_desc);
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
    
    //Create a buffer of users choice

    printf("\n----------------------------------------------------------------------------------------------");  
    printf("\nfill buffer with data from file\n");

    FILE *infile = fopen("scripts/resnet_test/USB_inst.txt", "r");
    FILE *outfile = fopen("streamOUT.txt", "w");
    char *line = NULL;
    size_t len = 0;
    ssize_t read_err;

    int loc;

    //buffer[1024 * 16] = '\0';
    while(1){
        for(int index = 0; index < 1024 * 16; index=index+4) {

            if(index >= 256 && index < 1024 * 16 - 256) {
                //printf("%d\n", index);
                read_err = getline(&line, &len, infile);

                //printf("\n%s\n", line);
                
                // for( i = 0; i < 32; i++) {
                //     reverse_line[i] = line[31-i];
                // }

                if(read_err == -1){
                    printf("\nfile end reached\n"); 
                    //release the interface claimed earlier
                    err = libusb_release_interface (dev_handle, 0);     
                    if(err)
                    {
                        printf("\nThe device interface is not getting released, if system hangs please disconnect the device, returning");
                        return;
                    }
                    fclose(infile);
                    return;
                }
                
                //if(index == 0) cout << line << endl;
                //cout << line << endl;
                char word_1[9], word_2[9], word_3[9], word_4[9];
                for(loc = 0; loc < 8; loc++){
                    word_1[loc] = line[loc];
                    word_2[loc] = line[loc + 8];
                    word_3[loc] = line[loc + 16];
                    word_4[loc] = line[loc + 24];
                }
                word_1[8] = '\0';
                word_2[8] = '\0';
                word_3[8] = '\0';
                word_4[8] = '\0';

                //cout << word_4 << "; " << word_3 << "; " << word_2 << "; " << word_1 << endl;
                
                //printf_binary(line);
                unsigned char c_1 = (unsigned char)(strtol(word_1, 0, 2) & 0xFF);
                unsigned char c_2 = (unsigned char)(strtol(word_2, 0, 2) & 0xFF);
                unsigned char c_3 = (unsigned char)(strtol(word_3, 0, 2) & 0xFF);
                unsigned char c_4 = (unsigned char)(strtol(word_4, 0, 2) & 0xFF);
                //if(index == 0){
                //printf("\n%d\t%d\t%d\t%d\n", c_1, c_2, c_3, c_4);
                //}
                buffer[index] = c_4;
                buffer[index+1] = c_3;
                buffer[index+2] = c_2;
                buffer[index+3] = c_1;

                //printf_binary(buffer[index+3]);
                //printf_binary(buffer[index+2]);
                //printf_binary(buffer[index+1]);
                //printf_binary(buffer[index+0]);
                //printf("\n");

                //fprintf_binary(outfile, buffer[index+3]);
                //fprintf_binary(outfile, buffer[index+2]);
                //fprintf_binary(outfile, buffer[index+1]);
                //fprintf_binary(outfile, buffer[index+0]);

                //fprintf(outfile, "\n");
            } else {
                buffer[index] = (unsigned char)0x72;
                buffer[index+1] = (unsigned char)0x01;
                buffer[index+2] = (unsigned char)0x00;
                buffer[index+3] = (unsigned char)0xC2;
            }
        }

        printf("\nbuffer prepared");

        transffered_bytes = 0;

        printf("\nbuffer prepared again");

        //usleep(1000000);

        while(1){

            printf("\nbuffer prepared again again");
            //cout << glOutMaxPacketSize << endl;
            //printf("\nTransffering %d bytes from HOST(PC) -> TARGET(Bulkloop device)", glOutMaxPacketSize);
            //err = libusb_bulk_transfer(dev_handle,glOutEpNum,out_data_buf,glOutMaxPacketSize,&transffered_bytes,1000000000); 
            err = libusb_bulk_transfer(dev_handle,glOutEpNum,buffer,glOutMaxPacketSize * 16,&transffered_bytes,0);  
            //err = libusb_bulk_transfer(dev_handle,glOutEpNum,out_data_buf,512,&transffered_bytes,1000000000); 
            if(err)
            {
                printf("\nBytes transffres failed, err: %d transffred bytes : %d",err,transffered_bytes); 
                //return;
            } else {
                
                printf("\nTransffred bytes : %d",transffered_bytes); 
                break;
            }
        }
        
        printf("\n\n-------------------------------------------------------------------------------------------------------------");
        printf("\n\nStreamOUT transfers completed successfully:");
        printf("\nData Transffered: %d bytes \n\n", transffered_bytes);

        //for(i=0; i < (int)transffered_bytes; i++)
        //    printf("%d\t",buffer[i]);
        //printf("\n\n-------------------------------------------------------------------------------------------------------------\n\n"); 

        //printf("new package\n");
    }
}

void  streamIN_transfer()
{
    int err;
    int i;
    int usr_choice,data_byte;
    int transffered_bytes; //actual transffered bytes
    unsigned char in_data_buf[1024];
    unsigned char in_row_buf[4];
    int index;
    //struct libusb_device_descriptor desc;
    unsigned char enum_glInEpNum=0;
	

    printf("\n-------------------------------------------------------------------------------------------------");  
    printf("\nThis function is for testing the bulk transfers. It will read from IN endpoint");
    printf("\n-------------------------------------------------------------------------------------------------");      

    //detect the bulkloop is running from VID/PID 
    err = libusb_get_device_descriptor(device, &main_desc);
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

    while(1) {

        printf("\n-------------------------------------------------------------------------------------------------");  
        transffered_bytes = 0;
        printf("\nTransfering %d bytes from TARGET(Bulkloop device) -> HOST(PC)", glInMaxPacketSize);
        //for(enum_glInEpNum = 0; enum_glInEpNum < 32; enum_glInEpNum = enum_glInEpNum+1){
        //err = libusb_bulk_transfer(dev_handle,enum_glInEpNum,in_data_buf,glInMaxPacketSize,&transffered_bytes,100);
        err = libusb_bulk_transfer(dev_handle,glInEpNum,in_data_buf,glInMaxPacketSize,&transffered_bytes,1000000);
        if(err)
        {

            printf("\nBulk IN Endpoint 0x%02x\n", enum_glInEpNum);
            printf("\nTransffer failed, err: %d transffred bytes : %d",err,transffered_bytes);
            //return;
        }     
    
     //}
        printf("\n\n------------------------------------------------------------------------------------------------------------------");
        printf("\n\nData Received: %d bytes\n\n", transffered_bytes);
        printf("\n\nwriting to StreamIn.txt\n\n");
        for(i=0; i < (int)transffered_bytes; i++){
            printf("%d\t",in_data_buf[i]);
            //fprintf(f, "%d\t", in_data_buf[i]);
            index = i%4;
            in_row_buf[3 - index] = in_data_buf[i]; 
            //fprintf_binary(f, in_data_buf[i]);

            if(index == 3) {
                fprintf_binary(f, in_data_buf[i]);
                fprintf_binary(f, in_data_buf[i-1]);
                fprintf_binary(f, in_data_buf[i-2]);
                fprintf_binary(f, in_data_buf[i-3]);
                fprintf(f, "\n");
            }
        }
    }

     printf("\n\n------------------------------------------------------------------------------------------------------------------\n\n");     
     fclose(f);
     
     //release the interface claimed earlier
     err = libusb_release_interface (dev_handle, 0);     
     if(err)
     {
        printf("\nThe device interface is not getting released, if system hangs please disconnect the device, returning");
        return;
     }
}

//void* streamOUT_transfer_parallel(void *)
//{
//    int err;
//    int transffered_bytes; //actual transffered bytes
//    while (1) {
//        transffered_bytes = 0;
//        pthread_mutex_lock(&transfer_lock);
//        while(!transfer_buffer_prepared) {
//            pthread_cond_wait(&transfer_cond, &transfer_lock);
//        }
//        pthread_mutex_lock(&prepare_lock);
//        while(1){
//            err = libusb_bulk_transfer(dev_handle,glOutEpNum,transfer_buffer,glOutMaxPacketSize * 16,&transffered_bytes,0);  
//            if(err)
//            {
//            } else {
//                transfer_buffer_prepared = false;
//                pthread_cond_signal(&prepare_cond);
//                pthread_mutex_unlock(&prepare_lock);
//                pthread_mutex_unlock(&transfer_lock);
//                break;
//            }
//        }
//    }
//    return NULL;
//}

#endif
