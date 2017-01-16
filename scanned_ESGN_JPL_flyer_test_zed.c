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
#define WITH_BUFFER   

using namespace std;
using namespace cv;

const int bug_row = 0;
const int bug_col = 349;

int _count;
float write_start_time = 0;
float write_stream_time_1 = 0;
float write_stream_time_1_1 = 0;
float write_stream_time_1_2 = 0;
float write_stream_time_1_0 = 0;
float write_stream_time_2 = 0;
Mat left_read, right_read;
void to_buffer(uint32_t bin){
    uint32_t trash = 0b11000010000000000000000000001010;
    int iner_count = _count%256;
    if(bin == 0b11011100000000000000000000000001 && iner_count > 200) {
        int num_zeros_to_insert = 256 - iner_count;
        while ( num_zeros_to_insert > 0 ) {
            for(int i = 0; i < 4; i++){
                buffer[_count * 4 + i] = (unsigned char)(trash >> i*8) & 0xFF;
            }
            num_zeros_to_insert--;
            _count++;
        }
        //transfer current
        if(_count == 4096) {
            pthread_mutex_lock(&prepare_lock);
            while(transfer_buffer_prepared) {
                pthread_cond_wait(&prepare_cond, &prepare_lock);
            }

            pthread_mutex_lock(&transfer_lock);
            memcpy ( transfer_buffer, buffer, 16 * 1024 * sizeof(unsigned char) );
            transfer_buffer_prepared = true;
            //unlock for the transfer
            pthread_cond_signal(&transfer_cond);
            pthread_mutex_unlock(&transfer_lock);

            pthread_mutex_unlock(&prepare_lock);
            _count = 0;
        }

        //insert 6 zeros in front
        for(int i = 0; i < 4; i++){
            buffer[_count * 4 + i] = (unsigned char)(trash >> i*8) & 0xFF;
        }
        _count++;
        for(int i = 0; i < 4; i++){
            buffer[_count * 4 + i] = (unsigned char)(trash >> i*8) & 0xFF;
        }
        _count++;
        for(int i = 0; i < 4; i++){
            buffer[_count * 4 + i] = (unsigned char)(trash >> i*8) & 0xFF;
        }
        _count++;
        for(int i = 0; i < 4; i++){
            buffer[_count * 4 + i] = (unsigned char)(trash >> i*8) & 0xFF;
        }
        _count++;
        for(int i = 0; i < 4; i++){
            buffer[_count * 4 + i] = (unsigned char)(trash >> i*8) & 0xFF;
        }
        _count++;
        for(int i = 0; i < 4; i++){
            buffer[_count * 4 + i] = (unsigned char)(trash >> i*8) & 0xFF;
        }
        _count++;
    }

    #ifdef WITH_BUFFER
    for(int i = 0; i < 4; i++){
        buffer[_count * 4 + i] = (unsigned char)(bin >> i*8) & 0xFF;
    }
    #endif

    _count++;

    if(_count == 4096) {
        pthread_mutex_lock(&prepare_lock);
        while(transfer_buffer_prepared) {
            pthread_cond_wait(&prepare_cond, &prepare_lock);
        }

        pthread_mutex_lock(&transfer_lock);
        memcpy ( transfer_buffer, buffer, 16 * 1024 * sizeof(unsigned char) );
        transfer_buffer_prepared = true;
        //unlock for the transfer
        pthread_cond_signal(&transfer_cond);
        pthread_mutex_unlock(&transfer_lock);
        pthread_mutex_unlock(&prepare_lock);
        _count = 0;
    }

}

string HexToBin(string s){
    const int num_of_bits = 12;
    stringstream ss;
    ss << hex << s;
    unsigned n;
    ss >> n;
    return bitset<num_of_bits>(n).to_string();
}

#ifdef WRITE_FILE
void write_vectr_file_start(fstream& vector_file){
#else
void write_vectr_file_start(){
#endif
    #ifdef MEASURE_DETAIL
    clock_t write_start_start = clock();
    #endif

    for(int x=0; x <100; x++){
        to_buffer(0b00000000000000000000000000000000);
    }


    to_buffer(0b11000010000000000000000000001010);//P1 10
    to_buffer(0b11000011000000000000000001100100);//P2 100
    to_buffer(0b11000100000000000000000000110001);//max_local_costs 49
    to_buffer(0b11000101000000000000001100100000);//max_global_costs 1000//800
    to_buffer(0b11000110000000000000000100101100);//average_cost 500//300
    to_buffer(0b11000111000000000000000000000000);//window_index 0
    to_buffer(0b11001000000000000000000000000000);//max_disp_index 0
    to_buffer(0b11001001000000000000001001000101);//max_img_size 589-8
    //to_buffer(0b11001001000000000000001011101000);//max_img_size  //752-8
    //to_buffer(0b11001001000000000000011110000000);//max_img_size 1920
    //to_buffer(0b11001001000000000000011100000010);//max_img_size 1794
    //SD
    to_buffer(0b11001010000000000000000000001100);//"SD1 //1111
    to_buffer(0b11001011000000000000000000001100);//"SD2 /1000 //1100
    to_buffer(0b11001100000000000000000000000100);//"SD3 //1000 //0100    //read
    to_buffer(0b11001101000000000000000000010000);//"SD4 //10010 //1111   //write
    to_buffer(0b11001110000000000000000000000100);//"SD5 /1100 //0100     //write end
    //for PLL
    to_buffer(0b11001111000000000000000000000000);//"pll_R
    to_buffer(0b11010000000000000000000000010100);//"pll_F
    to_buffer(0b11010001000000000000000000000000);//"pll_BP
    //empty PD
    to_buffer(0b11010010000000000000000000000000);//pll_BS
    //can't program OD
    to_buffer(0b11010011000000000000000000000010);//pll_OD
    to_buffer(0b11010100000000000000000000000100);//p_div
    to_buffer(0b11010101000000000000000000000011);//sgm_div
    to_buffer(0b11010110000000000000000000000000);//pll_PD
    to_buffer(0b11010111000000000000000000000001);//oscEn
    to_buffer(0b11011000000000000000000000000001);//selpllOscb
    to_buffer(0b11011001000000000000000000000100);//oscTune
    to_buffer(0b11011010000000000000000000000100);//RO_div
    to_buffer(0b11011011000000000000000000000001);//int_clk_sel
    to_buffer(0b11011101000000000000000000000000);//bi_dir
    #ifdef WRITE_FILE
    vector_file << bitset<32>(0b11000010000000000000000000001010) << endl;//P1 10
    vector_file << bitset<32>(0b11000011000000000000000001100100) << endl;//P2 100
    vector_file << bitset<32>(0b11000100000000000000000000110001) << endl;//max_local_costs 49
    vector_file << bitset<32>(0b11000101000000000000001111101000) << endl;//max_global_costs 1000//800
    vector_file << bitset<32>(0b11000110000000000000000100101100) << endl;//average_cost 500//300
    vector_file << bitset<32>(0b11000111000000000000000000000000) << endl;//window_index 0
    vector_file << bitset<32>(0b11001000000000000000000000000000) << endl;//max_disp_index 0
    vector_file << bitset<32>(0b11001001000000000000001001001101) << endl;//max_img_size 589
    //SD
    vector_file << bitset<32>(0b11001010000000000000000000001000) << endl;//"SD1
    vector_file << bitset<32>(0b11001011000000000000000000001100) << endl;//"SD2
    vector_file << bitset<32>(0b11001100000000000000000000000110) << endl;//"SD3
    vector_file << bitset<32>(0b11001101000000000000000000001111) << endl;//"SD4
    vector_file << bitset<32>(0b11001110000000000000000000000100) << endl;//"SD5
    //for PLL
    vector_file << bitset<32>(0b11001111000000000000000000000000) << endl;//"pll_R
    vector_file << bitset<32>(0b11010000000000000000000000010100) << endl;//"pll_F
    vector_file << bitset<32>(0b11010001000000000000000000000000) << endl;//"pll_BP
    //empty PD
    vector_file << bitset<32>(0b11010010000000000000000000000000) << endl;//pll_BS
    //can't program OD
    vector_file << bitset<32>(0b11010011000000000000000000000010) << endl;//pll_OD
    vector_file << bitset<32>(0b11010100000000000000000000000100) << endl;//p_div
    vector_file << bitset<32>(0b11010101000000000000000000000011) << endl;//sgm_div
    vector_file << bitset<32>(0b11010110000000000000000000000000) << endl;//pll_PD
    vector_file << bitset<32>(0b11010111000000000000000000000001) << endl;//oscEn
    vector_file << bitset<32>(0b11011000000000000000000000000001) << endl;//selpllOscb
    vector_file << bitset<32>(0b11011001000000000000000000000100) << endl;//oscTune
    vector_file << bitset<32>(0b11011010000000000000000000000100) << endl;//RO_div
    vector_file << bitset<32>(0b11011011000000000000000000000001) << endl;//int_clk_sel
    vector_file << bitset<32>(0b11011101000000000000000000000000) << endl;//bi_dir
    #endif

    #ifdef MEASURE_DETAIL
    clock_t write_start_end = clock();
    write_start_time += (float)(write_start_end - write_start_start)/CLOCKS_PER_SEC;
    #endif
}

#ifdef WRITE_FILE
void write_vector_file_stream(fstream& vector_file, Mat &left_image, Mat &right_image, int frameCounter, int row_counter, int col_counter, bool even, int& result_mem_even, int& image_mem_even){
#else
void write_vector_file_stream(Mat &left_image, Mat &right_image, int frameCounter, int row_counter, int col_counter, bool even, int& result_mem_even, int& image_mem_even){
#endif
    int row_num = 0;
    int col_num = 0;
    const int num_of_bits = 12;

    string output_string_1;
    string output_string_2;

    //left
    if(((row_counter == 0 && col_counter == 0) || (row_counter == 0 && col_counter == 1)) && frameCounter == 0){
    }
    else{
        if(row_counter == 0 && col_counter == 2 && (frameCounter % 1 == 0)) { //transfer one outstanding packet
            uint32_t control_result = 0;

            control_result = (uint32_t) 0x00000F00 |
                (0b1100000111100 << 19) | 
                (result_mem_even << 18);

            for(int m = 0; m < 6; m++) {
                to_buffer(control_result); 
            }
        } else if(row_counter == 0 && col_counter == 2 && (frameCounter % 1 != 0)) {
            uint32_t control_result = 0;

            control_result = (uint32_t) 0x00000700 |
                (0b1100000111100 << 19) | 
                (result_mem_even << 18);

            for(int m = 0; m < 6; m++) {
                to_buffer(control_result); 
            }
        }

        uint32_t control_result = 0;

        control_result = (uint32_t) 0 |
            (0b1100000111100 << 19) | 
            (result_mem_even << 18);

        for(int m = 0; m < 6; m++) {
            to_buffer(control_result); 
        } 
        #ifdef WRITE_FILE
        vector_file << bitset<32>(control_result) << endl;
        #endif
    }

    #ifdef MEASURE_DETAIL
    clock_t write_stream_start_1 = clock();
    #endif
    for(col_num = 0; col_num < 50; col_num++){
        #ifdef MEASURE_DETAIL
        clock_t write_stream_start_1_0 = clock();
        #endif
        
        uint32_t control_left = 0;
        control_left = control_left |
            (0b1100000011011 << 19) |
            (image_mem_even << 18) |
            (col_num << 6) |
            0b010011;

        to_buffer(control_left);
        #ifdef WRITE_FILE
        vector_file << bitset<32>(control_left) << endl;
        #endif

        #ifdef MEASURE_DETAIL
        clock_t write_stream_end_1_0 = clock();
        write_stream_time_1_0 += (float)(write_stream_end_1_0 - write_stream_start_1_0)/CLOCKS_PER_SEC;
        #endif
       
        for(int i = 0; i < 10; i++){

            #ifdef MEASURE_DETAIL
            clock_t write_stream_start_1_1 = clock();
            #endif

            uint32_t out_1 = 0;
            uint32_t out_2 = 0;
       
            out_1 = out_1 | 
                left_image.at<uint8_t>(5 * i + 0, col_num) |
                ((uint32_t)left_image.at<uint8_t>(5 * i + 1, col_num) << num_of_bits) |
                (((uint32_t)left_image.at<uint8_t>(5 * i + 2, col_num) & 0x3F) << 2*num_of_bits) |
                0x80000000;

            out_2 = out_2 | 
                (((uint32_t)left_image.at<uint8_t>(5 * i + 2, col_num) & 0xC0) >> 6) |
                ((uint32_t)left_image.at<uint8_t>(5 * i + 3, col_num) << 6)|
                (((uint32_t)left_image.at<uint8_t>(5 * i + 4, col_num)) << 18) |
                0x80000000;

            #ifdef MEASURE_DETAIL
            clock_t write_stream_end_1_1 = clock();
            write_stream_time_1_1 += (float)(write_stream_end_1_1 - write_stream_start_1_1)/CLOCKS_PER_SEC;
            #endif
	    #ifdef MEASURE_DETAIL
            clock_t write_stream_start_1_2 = clock();
            #endif
            to_buffer(out_1);
            to_buffer(out_2);
            #ifdef WRITE_FILE
            vector_file << bitset<32>(out_1) << endl;
            vector_file << bitset<32>(out_2) << endl;
            #endif

            #ifdef MEASURE_DETAIL
            clock_t write_stream_end_1_2 = clock();
            write_stream_time_1_2 += (float)(write_stream_end_1_2 - write_stream_start_1_2)/CLOCKS_PER_SEC;
            #endif

        }     
    }

    //right
    for(col_num = 0; col_num < 50; col_num++){

        #ifdef MEASURE_DETAIL
        clock_t write_stream_start_1_0 = clock();
        #endif
        uint32_t control_right = 0;
        control_right = control_right |
            (0b1100000011010 << 19) |
            (image_mem_even << 18) |
            (col_num << 6) |
            0b010011;


        to_buffer(control_right);
        #ifdef WRITE_FILE
        vector_file << bitset<32>(control_right) << endl;
        #endif

        #ifdef MEASURE_DETAIL
        clock_t write_stream_end_1_0 = clock();
        write_stream_time_1_0 += (float)(write_stream_end_1_0 - write_stream_start_1_0)/CLOCKS_PER_SEC;
        #endif

        for(int i = 0; i < 10; i++){

            #ifdef MEASURE_DETAIL
            clock_t write_stream_start_1_1 = clock();
            #endif

            uint32_t out_1 = 0;
            uint32_t out_2 = 0;
	    out_1 = out_1 | 
                right_image.at<uint8_t>(5 * i + 0, col_num) |
                ((uint32_t)right_image.at<uint8_t>(5 * i + 1, col_num) << num_of_bits)|
                (((uint32_t)right_image.at<uint8_t>(5 * i + 2, col_num) & 0x3F) << 2*num_of_bits) |
                0x80000000;

            out_2 = out_2 | 
                (((uint32_t)right_image.at<uint8_t>(5 * i + 2, col_num) & 0xC0) >> 6) |
                ((uint32_t)right_image.at<uint8_t>(5 * i + 3, col_num) << 6)|
                (((uint32_t)right_image.at<uint8_t>(5 * i + 4, col_num)) << 18) |
                0x80000000;

        #ifdef MEASURE_DETAIL
            clock_t write_stream_end_1_1 = clock();
            write_stream_time_1_1 += (float)(write_stream_end_1_1 - write_stream_start_1_1)/CLOCKS_PER_SEC;

            clock_t write_stream_start_1_2 = clock();
        #endif
            to_buffer(out_1);
            to_buffer(out_2);
            #ifdef WRITE_FILE
            vector_file << bitset<32>(out_1) << endl;
            vector_file << bitset<32>(out_2) << endl;
            #endif

        #ifdef MEASURE_DETAIL
            clock_t write_stream_end_1_2 = clock();
            write_stream_time_1_2 += (float)(write_stream_end_1_2 - write_stream_start_1_2)/CLOCKS_PER_SEC;
        #endif


        }     
    }
    
    #ifdef MEASURE_DETAIL
    clock_t write_stream_end_1 = clock();

    write_stream_time_1 += (float)(write_stream_end_1 - write_stream_start_1)/CLOCKS_PER_SEC;

    clock_t write_stream_start_2 = clock();
    #endif

        
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
        
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
        
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
        
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    to_buffer(0b00000000000000000000000000000000); //max_img_size
    #ifdef WRITE_FILE
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
        
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
        
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
        
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    #endif

       
       
    if(row_counter == 0 && col_counter == 0 && frameCounter == 0){
        //doest stop write on first image
        //initializing
        

    } else {
        to_buffer(0b11011100000000000000000000000001); //stop read
        #ifdef WRITE_FILE
        vector_file << bitset<32>(0b11011100000000000000000000000001) << endl;
        #endif
    }


    if(result_mem_even == 1){
        result_mem_even = 0;
    }
    else{
        result_mem_even = 1;
    }

    if(image_mem_even == 1){
        image_mem_even = 0;
    }
    else{
        image_mem_even = 1;
    } 

    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    to_buffer(0b00000000000000000000000000000000);//max_img_size
    #ifdef WRITE_FILE
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
        
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
        
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
        
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
    #endif


    
    #ifdef MEASURE_DETAIL
    clock_t write_stream_end_2 = clock();
    write_stream_time_2 += (float)(write_stream_end_2 - write_stream_start_2)/CLOCKS_PER_SEC;
    #endif

}

void write_vector_file(int row_max, int col_max){
    int num_of_bits = 12;
    int scale = 16;
    int row_num = 0;
    int col_num = 0;
    int image_mem_even = 0;
    int result_mem_even = 0;

    char vector_file_name[1024];
    char left_image_name[1024];
    char right_image_name[1024];
    char imageCounter_string[1024];
    
    int imageCounter;
    int rowCounter;
    int colCounter;

    fstream vector_file;
    fstream left_image;
    fstream right_image;

    string pixel_0, bin_pixel_0;
    string pixel_1, bin_pixel_1;
    string pixel_2, bin_pixel_2;
    string pixel_3, bin_pixel_3;
    string pixel_4, bin_pixel_4;

    string output_string_1;
    string output_string_2;

    for(imageCounter = 977; imageCounter < 978; imageCounter++){
        if(imageCounter < 10){
            sprintf(imageCounter_string, "00000%d_rect_l.png", imageCounter);
        }
        else if (imageCounter < 100){
            sprintf(imageCounter_string, "0000%d_rect_l.png", imageCounter);
        }
        else if (imageCounter < 1000){
            sprintf(imageCounter_string, "000%d_rect_l.png", imageCounter);
        }

        sprintf(vector_file_name, "input_datastream/stixel_1/vector_file_000%s.txt", imageCounter_string);
        vector_file.open(vector_file_name, fstream::out);

        vector_file << "11000010000000000000000000001010\n";//P1 10
        vector_file << "11000011000000000000000001100100\n";//P2 100
        vector_file << "11000100000000000000000000110001\n";//max_local_costs 49
        vector_file << "11000101000000000000001100100000\n";//max_global_costs 1000//800
        vector_file << "11000110000000000000000100101100\n";//average_cost 500//300
        vector_file << "11000111000000000000000000000000\n";//window_index 0
        vector_file << "11001000000000000000000000000000\n";//max_disp_index 0
        vector_file << "11001001000000000000001001001101\n";//max_img_size 589
        //SD
        vector_file << "11001010000000000000000000001100\n";//"SD1
        vector_file << "11001011000000000000000000001100\n";//"SD2
        vector_file << "11001100000000000000000000001100\n";//"SD3
        vector_file << "11001101000000000000000000001100\n";//"SD4
        vector_file << "11001110000000000000000000001100\n";//"SD5
        //for PLL
        vector_file << "11001111000000000000000000000000\n";//"pll_R
        vector_file << "11010000000000000000000000010100\n";//"pll_F
        vector_file << "11010001000000000000000000000000\n";//"pll_BP
        //empty PD
        vector_file << "11010010000000000000000000000000\n";//pll_BS
        //can't program OD
        vector_file << "11010011000000000000000000000010\n";//pll_OD
        vector_file << "11010100000000000000000000000100\n";//p_div
        vector_file << "11010101000000000000000000000011\n";//sgm_div
        vector_file << "11010110000000000000000000000000\n";//pll_PD
        vector_file << "11010111000000000000000000000001\n";//oscEn
        vector_file << "11011000000000000000000000000001\n";//selpllOscb
        vector_file << "11011001000000000000000000000100\n";//oscTune
        vector_file << "11011010000000000000000000000100\n";//RO_div
        vector_file << "11011011000000000000000000000001\n";//int_clk_sel
        
        for(rowCounter = 0; rowCounter < row_max; rowCounter++){
            for(colCounter = 0; colCounter < col_max; colCounter++){
                sprintf(left_image_name, "input_mem/stixel_0/left_image_000000%s_row_%d_col_%d.mem", imageCounter_string, rowCounter, colCounter);
                //cout << left_image_name << endl;

                left_image.open(left_image_name, fstream::in);
                row_num = 0;

                if((rowCounter == 0 && colCounter == 0) || (rowCounter == 0 && colCounter == 1)){
                    cout << "first" << endl;
                }
                else{
                    string control_result_string = "1100000111100" + to_string(result_mem_even) + "000000" + "000000" + "000000"; //control write left
                    vector_file << control_result_string << "\n";
                }

                string line;

                getline(left_image, line);
                while(!left_image.eof()){

                    string bin_row_num = bitset<6>(row_num).to_string();
                    string control_left_string = "1100000011011" + to_string(image_mem_even) + "000000" + bin_row_num + "010011"; //control write right
                    vector_file << control_left_string << "\n";
                    row_num++;

                    vector<string> split_line;
                    stringstream ss(line);
                    string hex;
                    ss >> hex;
                    while(!ss.eof()){
                        split_line.push_back(hex);
                        ss >> hex;
                    }
                    //cout << split_line.size() << endl;
            

                    for(int i = 0; i < 10; i++){
                        pixel_0 = split_line[i * 5 + 0];
                        bin_pixel_0 = HexToBin(pixel_0);
                        pixel_1 = split_line[i * 5 + 1];
                        bin_pixel_1 = HexToBin(pixel_1);
                        pixel_2 = split_line[i * 5 + 2];
                        bin_pixel_2 = HexToBin(pixel_2);
                        pixel_3 = split_line[i * 5 + 3];
                        bin_pixel_3 = HexToBin(pixel_3);
                        pixel_4 = split_line[i * 5 + 4];
                        bin_pixel_4 = HexToBin(pixel_4);
                        output_string_1 = "10"+ bin_pixel_2.substr(6, 6) + bin_pixel_1 + bin_pixel_0;
                        output_string_2 = "10" + bin_pixel_4 + bin_pixel_3 + bin_pixel_2.substr(0, 6);
                        vector_file << output_string_1 << "\n";
                        vector_file << output_string_2 << "\n";
                    }

                    getline(left_image, line);
                }

                left_image.close();

                sprintf(right_image_name, "input_mem/stixel_0/right_image_000000%s_row_%d_col_%d.mem", imageCounter_string, rowCounter, colCounter);
                right_image.open(right_image_name, fstream::in);
                row_num = 0;

                getline(right_image, line);
                while(!right_image.eof()){
                    string bin_row_num = bitset<6>(row_num).to_string();
                    string control_right_string = "1100000011010" + to_string(image_mem_even) + "000000" + bin_row_num + "010011"; //control write left
                    vector_file << control_right_string << "\n";
                    row_num++;

                    vector<string> split_line;
                    stringstream ss(line);
                    string hex;
                    ss >> hex;
                    while(!ss.eof()){
                        split_line.push_back(hex);
                        ss >> hex;
                    }
                    //cout << split_line.size() << endl;
 

                    for(int i = 0; i < 10; i++){
                        pixel_0 = split_line[i * 5 + 0];
                        bin_pixel_0 = HexToBin(pixel_0);
                        pixel_1 = split_line[i * 5 + 1];
                        bin_pixel_1 = HexToBin(pixel_1);
                        pixel_2 = split_line[i * 5 + 2];
                        bin_pixel_2 = HexToBin(pixel_2);
                        pixel_3 = split_line[i * 5 + 3];
                        bin_pixel_3 = HexToBin(pixel_3);
                        pixel_4 = split_line[i * 5 + 4];
                        bin_pixel_4 = HexToBin(pixel_4);
                        output_string_1 = "10"+ bin_pixel_2.substr(6, 6) + bin_pixel_1 + bin_pixel_0;
                        output_string_2 = "10" + bin_pixel_4 + bin_pixel_3 + bin_pixel_2.substr(0, 6);
                        vector_file << output_string_1 << "\n";
                        vector_file << output_string_2 << "\n";
                    }

                    getline(right_image, line);
                }

                right_image.close();

                vector_file << "00000000000000000000000000000000\n"; //max_img_size
                vector_file << "00000000000000000000000000000000\n"; //max_img_size
                vector_file << "00000000000000000000000000000000\n"; //max_img_size
                vector_file << "00000000000000000000000000000000\n"; //max_img_size
        
                vector_file << "00000000000000000000000000000000\n"; //max_img_size
                vector_file << "00000000000000000000000000000000\n"; //max_img_size
                vector_file << "00000000000000000000000000000000\n"; //max_img_size
                vector_file << "00000000000000000000000000000000\n"; //max_img_size
        
                vector_file << "00000000000000000000000000000000\n"; //max_img_size
                vector_file << "00000000000000000000000000000000\n"; //max_img_size
                vector_file << "00000000000000000000000000000000\n"; //max_img_size
                vector_file << "00000000000000000000000000000000\n"; //max_img_size
        
                if(rowCounter != 0 || colCounter != 0){
                    vector_file << "11011100000000000000000000000001\n"; //stop read
                }
        
                if(result_mem_even == 1){
                    result_mem_even = 0;
                }
                else{
                    result_mem_even = 1;
                }
        
                if(image_mem_even == 1){
                    image_mem_even = 0;
                }
                else{
                    image_mem_even = 1;
                }
        
                vector_file << "00000000000000000000000000000000\n";//max_img_size
                vector_file << "00000000000000000000000000000000\n";//max_img_size
                vector_file << "00000000000000000000000000000000\n";//max_img_size
                vector_file << "00000000000000000000000000000000\n";//max_img_size
        
                vector_file << "00000000000000000000000000000000\n";//max_img_size
                vector_file << "00000000000000000000000000000000\n";//max_img_size
                vector_file << "00000000000000000000000000000000\n";//max_img_size
                vector_file << "00000000000000000000000000000000\n";//max_img_size
        
                vector_file << "00000000000000000000000000000000\n";//max_img_size
                vector_file << "00000000000000000000000000000000\n";//max_img_size
                vector_file << "00000000000000000000000000000000\n";//max_img_size
                vector_file << "00000000000000000000000000000000\n";//max_img_size


            }
        }


        for(int i = 0; i < 100000; i++){
            vector_file << "00000000000000000000000000000000\n"; //max_img_size
        }



        vector_file.close();
    }


}

void write_test_image_mem(Mat &left_image, Mat &right_image, int frameCounter, int row_counter, int col_counter, bool even) {
    char left_img_mem_0_string[1024];
    char left_img_mem_1_string[1024];
    char right_img_mem_0_string[1024];
    char right_img_mem_1_string[1024];
    char left_raw_string[1024];
    char right_raw_string[1024];
    char frameCounter_string[1024];
    char col_counter_string[1024];
    char row_counter_string[1024];


    char left_block_string[1024];
    char right_block_string[1024];
    sprintf(left_block_string, "block/left_block_left_row_%d_col_%d.png", row_counter, col_counter);
    sprintf(right_block_string, "block/right_block_left_row_%d_col_%d.png", row_counter, col_counter);

    imwrite(left_block_string, left_image);
    imwrite(right_block_string, left_image);
    
    if(frameCounter < 10) {
        sprintf(frameCounter_string, "00000000%d", frameCounter);
    } else if (frameCounter >= 10 && frameCounter < 100){
        sprintf(frameCounter_string, "0000000%d", frameCounter);
    } else {
        sprintf(frameCounter_string, "000000%d", frameCounter);
    }
    sprintf(row_counter_string, "%d", row_counter);
    sprintf(col_counter_string, "%d", col_counter);
    sprintf(left_raw_string, "input_mem/stixel_0/left_image_%s_row_%s_col_%s.mem", frameCounter_string, row_counter_string, col_counter_string);
    sprintf(right_raw_string, "input_mem/stixel_0/right_image_%s_row_%s_col_%s.mem", frameCounter_string, row_counter_string, col_counter_string);
    
    ofstream left_raw_mem_file;
    ofstream right_raw_mem_file;

    left_raw_mem_file.open (left_raw_string);
    right_raw_mem_file.open (right_raw_string);
     
    //raw image
    for(int col = 0; col < 50; col++) {
        for(int row = 0; row < 50; row++) {
            ostringstream left_raw_mem;
            if(int(left_image.at<uint8_t>(row, col)) >= 16) {
                left_raw_mem << std::hex << '0' << int(left_image.at<uint8_t>(row, col));
                left_raw_mem_file << left_raw_mem.str() << ' ';
            } else {
                left_raw_mem << std::hex << '0' << '0' << int(left_image.at<uint8_t>(row, col));
                left_raw_mem_file << left_raw_mem.str() << ' ';
            }
        }
        left_raw_mem_file << endl;
    }
    for(int col = 0; col < 50; col++) {
        for(int row = 0; row < 50; row++) {
            ostringstream right_raw_mem;
            if(int(right_image.at<uint8_t>(row, col)) >= 16) {
                right_raw_mem << std::hex << '0' << int(right_image.at<uint8_t>(row, col));
                right_raw_mem_file << right_raw_mem.str() << ' ';
            } else {
                right_raw_mem << std::hex << '0' << '0' << int(right_image.at<uint8_t>(row, col));
                right_raw_mem_file << right_raw_mem.str() << ' ';
            }
        }
        right_raw_mem_file << endl;
    }
    
    left_raw_mem_file.close();
    right_raw_mem_file.close();
}

void write_result_image_mem(Mat &result_image, int frameCounter, int row_counter, int col_counter) {
    char result_mem_string[1024];
    char result_img_string[1024];
    char frameCounter_string[1024];
    char col_counter_string[1024];
    char row_counter_string[1024];
    if(frameCounter < 10) {
        sprintf(frameCounter_string, "00000%d", frameCounter);
    } else if (frameCounter >= 10 && frameCounter < 100){
        sprintf(frameCounter_string, "0000%d", frameCounter);
    } else {
        sprintf(frameCounter_string, "000%d", frameCounter);
    }
    sprintf(row_counter_string, "%d", row_counter);
    sprintf(col_counter_string, "%d", col_counter);
    sprintf(result_mem_string, "output_buffer/result_image_%s_row_%s_col_%s.mem", frameCounter_string, row_counter_string, col_counter_string);
    sprintf(result_img_string, "output_mem/result_raw_image_%s_row_%s_col_%s.mem", frameCounter_string, row_counter_string, col_counter_string);

    ofstream result_mem_file;
    ofstream result_img_file;
    result_mem_file.open (result_mem_string);
    result_img_file.open (result_img_string);
    
    for(int col = 0; col < 50; col++) {
        for(int row = 0; row < 50; row++) {
            ostringstream result_mem;
            ostringstream result_img;

            if(int(result_image.at<uint8_t>(row, col)) >= 100) {
                result_img << std::dec << int(result_image.at<uint8_t>(row, col));
                result_img_file << result_img.str() << ' ';
            } else if (int(result_image.at<uint8_t>(row, col)) < 100 && int(result_image.at<uint8_t>(row, col)) >= 10) {
                result_img << std::dec << '0' << int(result_image.at<uint8_t>(row, col));
                result_img_file << result_img.str() << ' ';
            } else {
                result_img << std::dec << '0' << '0' << int(result_image.at<uint8_t>(row, col));
                result_img_file << result_img.str() << ' ';
            }

            if(int(result_image.at<uint8_t>(row, col)) >= 16) {
                result_mem << std::hex << int(result_image.at<uint8_t>(row, col));
                result_mem_file << result_mem.str();
            } else {
                result_mem << std::hex << '0' << int(result_image.at<uint8_t>(row, col));
                result_mem_file << result_mem.str();
            }

            result_mem_file << endl;
        }
        result_img_file << endl;
    }
    result_mem_file.close();
    result_img_file.close();
}



void error_measure(Mat &Confidence, Mat &disparity, Mat &Ground_truth, Mat &outlinerMap){
    float error = 0;
    float confident_error = 0;
    int num = 0;
    int valid_num = 0;
    int confident_valid_num = 0;
    int error_num = 0;
    int confident_error_num = 0;
    float outliners = 0;
    float confident_outliners = 0;
    for (int row = 128; row < Ground_truth.rows; row++){
        for (int col = 128; col < Ground_truth.cols; col++){
            if(Ground_truth.at<uint8_t>(row, col) != 0) {
                    int difference = (int)disparity.at<uint8_t>(row, col) - (int)Ground_truth.at<uint8_t>(row, col);
                    if(difference > 0) {
                        error = error + difference;
                        if((int)Confidence.at<uint8_t>(row, col) > 6){
                            confident_error = confident_error + difference;
                        }
                        if(difference >= 4) {
                            outlinerMap.at<uint8_t>(row, col) = uint8_t(255);
                            if((int)Confidence.at<uint8_t>(row, col) > 6) {
                                confident_error_num++;
                            }
                            error_num++;
                        } else {
                            outlinerMap.at<uint8_t>(row, col) = disparity.at<uint8_t>(row, col);
                        }
                    }
                    else {
                        error = error - difference;
                        if(difference <= -4) {
                            outlinerMap.at<uint8_t>(row, col) = uint8_t(255);
                            if((int)Confidence.at<uint8_t>(row, col) > 6){
                                confident_error_num++;
                            }
                            error_num++;
                        } else {
                            outlinerMap.at<uint8_t>(row, col) = disparity.at<uint8_t>(row, col);
                        }
                    }
                    if((int)Confidence.at<uint8_t>(row, col) > 6){
                        confident_valid_num++;
                    }
                    valid_num++;
                num++;
            }    
        }
    }
    error = error/(float)valid_num;
    confident_error = confident_error/(float)confident_valid_num;
    outliners = (float)error_num/(float)valid_num;
    confident_outliners = (float)confident_error_num/(float)confident_valid_num;
    cout << "total: " << num << ", valid_num: " << valid_num << ", error_num: " << error_num << ", outliners: " << outliners << ", average error: " << error << endl; 
    
    return;
}

void distance_error_measure(Mat &Confidence, Mat &disparity, Mat &Ground_truth){
    float error = 0;
    int num = 0;
    int valid_num = 0;
    double error_counter = 0;
    float outliners = 0;
    for (int row = 0; row < Ground_truth.rows; row++){
        for (int col = 0; col < Ground_truth.cols; col++){
            if((int)Ground_truth.at<uint8_t>(row, col) != 0) {
                if(disparity.at<uint8_t>(row, col) != 0){
                    float gt_dist = 1/(float)Ground_truth.at<uint8_t>(row, col);
                    float dist = 1/(float)disparity.at<uint8_t>(row, col);
                    float difference = dist - gt_dist;

                    if(difference > 0) {
                        error = difference/gt_dist;
                    }
                    else {
                        error = (-1 * difference)/gt_dist;
                    }
                    if(error > 0) {
                        error_counter *= error;
                    } else {
                        error_counter *= error;
                    }
                    valid_num++;
                }
                num++;
            }    
        }
    }
    error_counter = pow(error_counter, 1.0/valid_num);
    cout << "total: " << num << ", valid_num: " << valid_num << ", avg_dist_error: " << error_counter << endl; 
    return;
}

uint64_t find_Lr_min(uint64_t Lr[], int disparity, int maxdisp){
    uint64_t min = uint64_t(1000000000);
    for(int i = 0; i < maxdisp; i++){
        if((i != disparity - 1) && (i != disparity + 1) && (i != disparity)) {
            if((int)Lr[i] < (int)min) {
                min = Lr[i];
            }
        }
    }
    return min;
}

uint64_t find_Lr_min_all(uint64_t Lr[], int maxdisp){
    uint64_t min = uint64_t(1000000000);
    for(int i = 0; i < maxdisp; i++){
        if((int)Lr[i] < (int)min) {
            min = Lr[i];
        }
    }
    return min;
}


uint8_t find_S_min_1(uint64_t S[], int maxdisp){
    uint8_t min;
    uint64_t cost = uint64_t(1000000);
    for(int i = 0; i < maxdisp; i++){
        if((int)S[i] < (int)cost) {
                min = (uint8_t)i;
                cost = (uint64_t)S[i];
        }
    }
    return min;
}

uint8_t find_S_min_2(uint64_t S[], int maxdisp, int min_1){
    uint8_t min;
    uint64_t cost = uint64_t(1000000);
    for(int i = 0; i < maxdisp; i++){
        if (i != min_1) {
            if((int)S[i] < (int)cost) {
                    min = (uint8_t)i;
                    cost = (uint64_t)S[i];
            }
        }
    }
    return min;
}

uint8_t find_S_min_3(uint64_t S[], int maxdisp, int min_1, int min_2){
    uint8_t min;
    uint64_t cost = uint64_t(100000);
    for(int i = 0; i < maxdisp; i++){
        if (i != min_1 && i != min_2) {
            if((int)S[i] < (int)cost) {
                    min = (uint8_t)i;
                    cost = (uint64_t)S[i];
            }
        }
    }
    return min;
}

uint64_t find_min(uint64_t A, uint64_t B, uint64_t C, uint64_t D){
    uint64_t min = A;
    if ((int)min > (int)B) {
        min = B;
    }
    if ((int)min > (int)C) {
        min = C;
    }
    if ((int)min > (int)D){
        min = D;
    }
    return min;
}



Mat census_trans (Mat A, int kernel_size) {
    Mat result = Mat::zeros(A.rows, A.cols, DataType<uint64_t>::type);
    int half_window = (kernel_size - 1)/2;
    for (int row = 0; row < A.rows; row++) {
        for (int col = 0; col < A.cols; col++) {
            for (int row_w = -1 * half_window; row_w <= half_window; row_w++) {
                for (int col_w = -1 * half_window; col_w <= half_window; col_w++) {
                    if(row_w != 0 || col_w != 0) {
                        if ((row + row_w < A.rows) && (col + col_w < A.cols) && (row + row_w >= 0) && (col + col_w >= 0)) { 
                            if (A.at<uint8_t>(row + row_w, col + col_w) < A.at<uint8_t>(row, col)) {
                                result.at<uint64_t>(row,col) = (uint64_t)(result.at<uint64_t>(row, col) | ((uint64_t) 1 << ((row_w + half_window) * kernel_size + col_w + half_window)));
                            }
                            else {
                            }
                        }
                        else {
                            
                        }
                    }
                    else {

                    }                
                }
            }
        }
    }
    return result;
}
       

void readIntrinsics(string filename, Mat cameraMatrix[2], Mat distCoeffs[2]){
    FileStorage fs(filename, FileStorage::READ);
    if(!fs.isOpened())
        cout << filename << " open failed!" << endl;

    FileNode n = fs["M1"];
    n >> cameraMatrix[0];
    n = fs["D1"];
    n >> distCoeffs[0];
    n = fs["M2"];
    n >> cameraMatrix[1];
    n = fs["D2"];
    n >> distCoeffs[1];
    fs.release();
}

void readExtrinsics(string filename, Mat& R, Mat& T, Mat& R1, Mat& R2, Mat& P1, Mat& P2, Mat& Q){
    FileStorage fs(filename, FileStorage::READ);
    if(!fs.isOpened())
        cout << filename << " open failed!" << endl;
    
    FileNode n = fs["R"];
    n >> R;
    n = fs["T"];
    n >> T;
    n = fs["R1"];
    n >> R1;
    n = fs["R2"];
    n >> R2;
    n = fs["P1"];
    n >> P1;
    n = fs["P2"];
    n >> P2;
    n = fs["Q"];
    n >> Q;
    
    fs.release();
   
}

void StereoCalib(Size imageSize, Rect validRoi[2], Mat rmap[2][2])
{
    
    int i, j, k;

    Mat cameraMatrix[2], distCoeffs[2];
    string fsIn = "intrinsics.yml";

    readIntrinsics(fsIn, cameraMatrix, distCoeffs);
    Mat R, T, R1, R2, P1, P2, Q;
    string fsEx = "extrinsics.yml";
    readExtrinsics(fsEx, R, T, R1, R2, P1, P2, Q);
    stereoRectify(cameraMatrix[0], distCoeffs[0],
                  cameraMatrix[1], distCoeffs[1],
                  imageSize, R, T, R1, R2, P1, P2, Q,
                  CALIB_ZERO_DISPARITY, 1, imageSize, &validRoi[0], &validRoi[1]);
    initUndistortRectifyMap(cameraMatrix[0], distCoeffs[0], R1, P1, imageSize, CV_16SC2, rmap[0][0], rmap[0][1]);
    initUndistortRectifyMap(cameraMatrix[1], distCoeffs[1], R2, P2, imageSize, CV_16SC2, rmap[1][0], rmap[1][1]);
}

struct Object {
    int image_num;
    Size imageSize;
    Rect validRoi[2];
    Mat rmap[2][2];
    Mat leftImage;
    Mat rightImage;
};

void CapImage(int image_num, Size imageSize, Rect validRoi[2], Mat rmap[2][2], Mat& leftImage, Mat& rightImage){
    
    int i, k;

    bool useCalibrated = true;

    Mat newcanvas;
    newcanvas.create(imageSize.height, imageSize.width * 2, CV_8UC3);
    int w = imageSize.width;
    int h = imageSize.height;

    Mat realImage;
    
    int rows = 480;
    int cols = 1280;
    
    for(i = 0; i < image_num; i++)
    {
        Mat frame;
        Mat left_gray = Mat::zeros(left_read.rows, left_read.cols, DataType<uint8_t>::type);
   
        for( k = 0; k < 2; k++ )
        {
            Mat img;
            if (k == 0) img = left_read.clone();
            else img = right_read.clone();
            Mat rimg, cimg;
            
            for(int row = 0; row < left_gray.rows; row++){
                for(int col = 0; col < left_gray.cols; col++){
                    left_gray.at<uint8_t>(row, col) = img.at<uint8_t>(row, col);      
                }
            }
            remap(img, rimg, rmap[k][0], rmap[k][1], INTER_LINEAR);   
            cimg = rimg.clone();
            
            Mat canvasPart = newcanvas(Rect(w*k, 0, w, h));
          
            resize(cimg, canvasPart, canvasPart.size(), 0, 0, INTER_AREA);
            
            if(k == 0){
                leftImage = canvasPart.clone();
            }
            else{
                rightImage = canvasPart.clone();
            }
            
            if( useCalibrated )
            {
                Rect vroi(validRoi[k].x, validRoi[k].y, validRoi[k].width, validRoi[k].height);
                rectangle(canvasPart, vroi, Scalar(0,0,255), 3, 8);
            } 
        }
       
        if(waitKey(30) >= 0) break;
    }

}


void* CapImage_helper(void *obj) {
        Object *cap_input = (Object *)obj;
        CapImage(cap_input->image_num, 
                cap_input->imageSize, 
                cap_input->validRoi, 
                cap_input-> rmap, 
                cap_input->leftImage, 
                cap_input->rightImage);
        return NULL;
}

int main () {

    pthread_t threads_0;
    pthread_t threads_1;//transfer thread
    pthread_t threads_2;//capture thread
    int irets[8];
    transfer_lock = PTHREAD_MUTEX_INITIALIZER;
    transfer_cond = PTHREAD_COND_INITIALIZER;
    prepare_lock = PTHREAD_MUTEX_INITIALIZER;
    prepare_cond = PTHREAD_COND_INITIALIZER;
    transfer_buffer_prepared = 0;

    process_lock = PTHREAD_MUTEX_INITIALIZER;
    process_cond = PTHREAD_COND_INITIALIZER;
    cap_lock = PTHREAD_MUTEX_INITIALIZER;
    cap_cond = PTHREAD_COND_INITIALIZER;
    cap_buffer_prepared = 0;

    float main_time = 0;
    #ifdef MEASURE_DETAIL
    float cap_time = 0;
    float prep_time = 0;
    float block_time = 0;
    float block_time_1 = 0;
    float block_time_2 = 0;
    float transfer_time = 0;
    float total_time = 0;
    float write_time = 0;
    #endif
    struct timeval main_start, main_end;

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

    //blocking
    const int subimg_rows = 50;
    const int subimg_cols = 50;
    const int overlap = 8;
    const int maxdisp = 128;
    int frameCounter = 0;
    char frameCounter_string[1024];
    char left_img_string[1024];
    char right_img_string[1024];

    int i, j, k;
    int image_num = 1;
     
    Size imageSize(640, 480); 
    Rect validRoi[2];
    Mat rmap[2][2];
    int cols=1280;
    Mat frame;
    VideoCapture cap(1);  //zed camera
    if(!cap.isOpened()){
	cout << "camera not open" <<endl;
	return 0;
    }
    //cap >> frame;
    //cvtColor(frame.clone(), frame, CV_BGR2GRAY);
   // Mat left_image_1(frame, Range::all(), Range(0, cols/2));
    //Mat right_image_1(frame, Range::all(), Range(cols/2, cols));
   // imwrite("zed_left.png",left_image_1);
    //imwrite("zed_right.png",right_image_1);
    //left_read = imread("left1.png", 0);
    //right_read = imread("right1.png", 0);
    //left_read(frame, Range::all(), Range(0, cols/2));
    //right_read(frame, Range::all(), Range(cols/2, cols));
    
    StereoCalib(imageSize, validRoi, rmap);
    int x = MAX(validRoi[0].x, validRoi[1].x);
    int y = MAX(validRoi[0].y, validRoi[1].y);
    int x_end = MIN(validRoi[0].x+validRoi[0].width, validRoi[1].x+validRoi[1].width);
    int y_end = MIN(validRoi[0].y+validRoi[0].height, validRoi[1].y+validRoi[1].height);
    int width = MIN(validRoi[0].x+validRoi[0].width, validRoi[1].x+validRoi[1].width) - x;
    int height = MIN(validRoi[0].y+validRoi[0].height, validRoi[1].y+validRoi[1].height) - y;
   // cout<<"x"<<x<<"y"<<y<<"x_end"<<x_end<<"y_end"<<y_end<<endl;
    int imageCounter;
    #ifdef WRITE_FILE
    char vector_file_name[1024];
    char imageCounter_string[1024];
    fstream vector_file;
    sprintf(vector_file_name, "vector_file_continuous.txt");
    vector_file.open(vector_file_name, fstream::out);
    #endif
   
    int image_mem_even = 0;
    int result_mem_even = 0;

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

    //creat a thread for transfer
    irets[1] = pthread_create(&threads_1, NULL, &streamOUT_transfer_parallel, NULL);

    //creat a thread for capture
    Object cap_input;
    //irets[2] = pthread_create(&threads_2, NULL, &CapImage_helper, &cap_input);

    gettimeofday(&main_start, NULL);

    int     row_shift = 0;
    int     col_shift = 0;
    int     next_row_shift = 0;
    int     next_col_shift = 0;
    int     subimage_counter = 0;
    int     even = 0;
    int     row_counter = 0;
    int     col_counter = 0;
        
    int     start_image = 120;
    for(imageCounter = 0; imageCounter < 2000; imageCounter++){
        
        cap >> frame;  //capture from zed camera
        //reset chip
        if(imageCounter == 0) {
            GPIO_init();
        }

        char left_image_string[1024];
        char right_image_string[1024];

        if(imageCounter + start_image < 10) {
            sprintf(left_image_string, "flyer/flyer_4/00000%d_rect_l.png", imageCounter + start_image);
            sprintf(right_image_string, "flyer/flyer_4/00000%d_rect_r.png", imageCounter + start_image);
        } else if (imageCounter + start_image >= 10 && imageCounter + start_image < 100){
            sprintf(left_image_string, "flyer/flyer_4/0000%d_rect_l.png", imageCounter + start_image);
            sprintf(right_image_string, "flyer/flyer_4/0000%d_rect_r.png", imageCounter + start_image);
        } else {
            sprintf(left_image_string, "flyer/flyer_4/000%d_rect_l.png", imageCounter + start_image);
            sprintf(right_image_string, "flyer/flyer_4/000%d_rect_r.png", imageCounter + start_image);
        }
        _count = 0;

        #ifdef MEASURE_DETAIL
        clock_t total_start = clock();
        clock_t cap_start = clock();
        #endif
        //Mat left_image = imread(left_image_string, CV_LOAD_IMAGE_GRAYSCALE);
        //Mat right_image = imread(right_image_string, CV_LOAD_IMAGE_GRAYSCALE);
        cvtColor(frame, frame, CV_BGR2GRAY);
       // cout<<"clone done"<<"frame_row"<<frame.rows<<"frame_cols"<<frame.cols<<"y"<<y<<"y_end"<<y_end<<"x"<<x<<"x_end"<<x_end<<"cols/2+x"<<cols/2+x<<endl;
	Mat left_image_raw(frame, Range::all(), Range(0, cols/2));
	Mat right_image_raw(frame, Range::all(), Range(cols/2, cols));
	//Mat left_image_raw= imread("left1.png");
	//Mat right_image_raw=imread("right1.png");
	left_read= left_image_raw.clone();
	right_read= right_image_raw.clone();
	CapImage(image_num, imageSize, validRoi, rmap, left_read, right_read);
	Rect region(x, y, width, height);
	Mat left_image(left_read, region);
	Mat right_image(right_read, region);
	//remap(left_image_raw, left_image_raw, rmap[k][0], rmap[k][1], INTER_LINEAR);
	//remap(right_image_raw, right_image_raw, rmap[k][0], rmap[k][1], INTER_LINEAR);
        imshow("left_image_raw",left_read);
	imshow("right_image_raw",right_read);
	//Mat left_image(left_image_raw, Range(y,y_end), Range(x, x_end));
	//Mat right_image(right_image_raw, Range(y,y_end), Range(x, x_end));

	//Size size(752,480);
	//resize(left_image,left_image, size);
	//resize(right_image, right_image, size);
	//left_image = imread(left_image_string, CV_LOAD_IMAGE_GRAYSCALE);
	//right_image = imread(right_image_string, CV_LOAD_IMAGE_GRAYSCALE);
	imshow("left_image",left_image);
	imshow("right_image",right_image);
        waitKey(1);
	//cout<<"initial image done"<<endl;
        cv::Mat imageGrey;
        cv::Mat imageArr[] = {left_image, left_image, left_image};
        cv::merge(imageArr, 3, imageGrey);
        //out_capture.write(imageGrey);
        Mat left_image_flip, right_image_flip;
        
        //imwrite("left_flip.png", left_image_flip);
        //imwrite("right_flip.png", right_image_flip);
        #ifdef MEASURE_DETAIL
        clock_t cap_end = clock();
        cap_time += (float) (cap_end - cap_start)/CLOCKS_PER_SEC;
        clock_t prep_start = clock();
        #endif
        
        /*liziyun
        Mat left_gray(left_image.clone());
        Mat right_gray(right_image.clone());
        */
        //HD only
        //Mat left_gray = imread("umich_HD_l.png", CV_LOAD_IMAGE_GRAYSCALE);
        //Mat right_gray = imread("umich_HD_r.png", CV_LOAD_IMAGE_GRAYSCALE);
        //
        /*
        Mat left_image = imread("umich_HD_l.png", CV_LOAD_IMAGE_GRAYSCALE);
        Mat right_image = imread("umich_HD_r.png", CV_LOAD_IMAGE_GRAYSCALE);
        */
        flip(left_image, left_image_flip, 1);
        flip(right_image, right_image_flip, 1);
        
        Mat left_gray = Mat::zeros(2 * left_image.rows, left_image.cols, DataType<uint8_t>::type);
        Mat right_gray = Mat::zeros(2 * left_image.rows, left_image.cols, DataType<uint8_t>::type);


        // left_gray = imread("left_rect_15.png", CV_LOAD_IMAGE_GRAYSCALE);
        // right_gray = imread("right_rect_15.png", CV_LOAD_IMAGE_GRAYSCALE);
        
        for(int row = 0; row < left_gray.rows; row++){
            for(int col = 0; col < left_gray.cols; col++){
                if(row < left_image.rows){
                    left_gray.at<uint8_t>(row, col) = left_image.at<uint8_t>(row, col);
                    right_gray.at<uint8_t>(row, col) = right_image.at<uint8_t>(row, col);
                }
                else{
                    left_gray.at<uint8_t>(row, col) = right_image_flip.at<uint8_t>(row - left_image.rows, col);
                    right_gray.at<uint8_t>(row, col) = left_image_flip.at<uint8_t>(row - left_image.rows, col);
                }
            }
        }

        #ifdef MEASURE_DETAIL
        clock_t prep_end = clock();
        prep_time += (float)(prep_end - prep_start)/CLOCKS_PER_SEC;
        #endif
        //imwrite("left_image.png", left_gray);
        //imwrite("right_image.png", right_gray);

        //imshow("image", left_gray);
        //waitKey(50);
        

        //return 0;

        //Mat left_gray_after_cen = census_trans(left_gray, 7);
        //Mat right_gray_after_cen = census_trans(right_gray, 7);
        Mat sub_left_gray = Mat::zeros(subimg_rows, subimg_cols, DataType<uint8_t>::type);
        Mat sub_right_gray = Mat::zeros(subimg_rows, subimg_cols, DataType<uint8_t>::type);

        row_shift = 0;
        col_shift = 0;
        next_row_shift = 0;
        next_col_shift = 0;
        subimage_counter = 0;
        even = 0;
        row_counter = 0;
        col_counter = 0;
        
        #ifdef MEASURE_DETAIL
        clock_t block_start = clock();
        #endif


        #ifdef WRITE_FILE
        if(imageCounter < 10){
            sprintf(imageCounter_string, "000%d", imageCounter);
        }
        else if (imageCounter < 100){
            sprintf(imageCounter_string, "00%d", imageCounter);
        }
        else if (imageCounter < 1000){
            sprintf(imageCounter_string, "0%d", imageCounter);
        } else {
            sprintf(imageCounter_string, "%d", imageCounter);
        }
        #endif

        #ifdef DISPLAY
        vector_file << "image: " << imageCounter << endl;
        write_vectr_file_start(vector_file);
        #else
        write_vectr_file_start();
        #endif

        #ifdef WRITE_FILE
        sprintf(left_img_string, "left_rect_00%s.png", imageCounter_string);
        sprintf(right_img_string, "right_rect_00%s.png", imageCounter_string);
        imwrite(left_img_string, left_gray);
        imwrite(right_img_string, right_gray);
        #endif
        
        if(imageCounter == 0) {
            //write GPIO
            irets[0] = pthread_create(&threads_0, NULL, &GPIO_write, NULL);

            //wait until reset, afifo_reset, debug are ready
            usleep(3100000);
        }

        while (row_shift < left_gray.rows - 1) {
            col_shift = 0;
            col_counter = 0;
            while (col_shift < left_gray.cols - 1){
                subimage_counter++;
                //cout << "work on row_shift: " << row_shift << endl;
                //cout << "work on col_shift: " << col_shift << endl;
                
                #ifdef MEASURE_DETAIL
                clock_t block_start_1 = clock();
                #endif
                
                if((subimg_rows + row_shift <= (left_gray.rows - 1)) && (subimg_cols + col_shift <= (left_gray.cols - 1))){

                    sub_left_gray = Mat(left_gray, Range(row_shift, row_shift + subimg_rows), Range(col_shift, col_shift + subimg_cols));
                    sub_right_gray = Mat(right_gray, Range(row_shift, row_shift + subimg_rows), Range(col_shift, col_shift + subimg_cols));
                } else {
                //@@@keep
                    for(int row = 0; row < subimg_rows; row ++) {
                        for(int col = 0; col < subimg_cols; col++) {
                            if((row + row_shift > (left_gray.rows - 1)) || (col + col_shift > (left_gray.cols - 1))){
                                //sub_left_gray_after_cen.at<uint64_t>(row, col) = 0;
                                sub_left_gray.at<uint8_t>(row, col) = 0;
                                sub_right_gray.at<uint8_t>(row, col) = 0;
                            } else {
                                //sub_left_gray_after_cen.at<uint64_t>(row, col) = left_gray_after_cen.at<uint64_t>(row + row_shift, col + col_shift);
                                sub_left_gray.at<uint8_t>(row, col) = left_gray.at<uint8_t>(row + row_shift, col + col_shift);
                                sub_right_gray.at<uint8_t>(row, col) = right_gray.at<uint8_t>(row + row_shift, col + col_shift);
                            }
                        }
                    }
                }
        
                #ifdef MEASURE_DETAIL
                clock_t block_end_1 = clock();

                block_time_1 += (float)(block_end_1 - block_start_1)/CLOCKS_PER_SEC;

                clock_t block_start_2 = clock();
                #endif
                   
                //@@@keep
                if(even == 1){ 
                    #ifdef WRITE_FILE
                    write_vector_file_stream(vector_file, sub_left_gray, sub_right_gray, imageCounter, row_counter, col_counter, 1, result_mem_even, image_mem_even);
                    #else
                    write_vector_file_stream(sub_left_gray, sub_right_gray, imageCounter, row_counter, col_counter, 1, result_mem_even, image_mem_even);
                    #endif
                    even = 0;
                } else {
                    #ifdef WRITE_FILE
                    write_vector_file_stream(vector_file, sub_left_gray, sub_right_gray, imageCounter, row_counter, col_counter, 0, result_mem_even, image_mem_even);
                    #else
                    write_vector_file_stream(sub_left_gray, sub_right_gray, imageCounter, row_counter, col_counter, 0, result_mem_even, image_mem_even);
                    #endif
                    even = 1;
                }
    		//imshow("sub_right_gray",sub_right_gray);
		//waitKey(1);
                #ifdef MEASURE_DETAIL
                clock_t block_end_2 = clock();
                block_time_2 += (float)(block_end_2 - block_start_2)/CLOCKS_PER_SEC;
                #endif
                //cout << row_counter << " " << col_counter << endl;
    
                next_col_shift = col_shift + subimg_cols - overlap;
                next_row_shift = row_shift + subimg_rows - overlap;
                                                 
                col_shift = next_col_shift;
                col_counter++;
            }
            row_shift = next_row_shift;
            row_counter++;
        }

        #ifdef MEASURE_DETAIL
        clock_t write_start = clock();
        #endif
        //indicate a frame end
        for(int i = 0; i < 4000; i++){
            to_buffer(0b00000000000000000000000000000000); //max_img_size
            #ifdef WRITE_FILE
            vector_file << bitset<32>(0b00000000000000000000000000000000) << endl; //max_img_size
            #endif
        }
        #ifdef MEASURE_DETAIL
        clock_t write_end = clock();

        write_time += (float)(write_end - write_start)/CLOCKS_PER_SEC;
        #endif

        //vector_file.close();

        #ifdef MEASURE_DETAIL
        clock_t block_end = clock();

        block_time += (float) (block_end - block_start)/CLOCKS_PER_SEC;

        clock_t transfer_start = clock();
        #endif

        //toggle controls
        //GPIO_write();
        //irets[0] = pthread_create(&threads_0, NULL, &GPIO_write, NULL);

        //wait until reset, afifo_reset, debug are ready
        //usleep(3100000);

        //cout << "finishing GPIO operation" << endl;
        //transfer
        //streamOUT_transfer();
        #ifdef MEASURE_DETAIL
        clock_t transfer_end = clock();
        transfer_time += (float)(transfer_end - transfer_start)/CLOCKS_PER_SEC;

        clock_t total_end = clock();
        total_time += (float)(total_end - total_start)/CLOCKS_PER_SEC;
        #endif

        //pthread_join();

    }

    //All tasks done close the device handle
    libusb_close(dev_handle);
    
    //Exit from libusb library
    libusb_exit(NULL);
    
    //clock_t main_end = clock();
    //main_time = (float)(main_end - main_start)/CLOCKS_PER_SEC;
    gettimeofday(&main_end, NULL);
    
    //for(int i = 0; i < 16; i++){
    //    for(int j = 0; j < 4; j++){
    //        cout << bitset<8>((int)(buffer[4*i + j])) << " ";
    //    }
    //    cout << endl;
    //}

    #ifdef MEASURE_DETAIL
    cout << "cap time: " << cap_time << endl;
    cout << "prep time: " << prep_time << endl;
    cout << "block time: " << block_time << endl;
    //cout << "block time 1: " << block_time_1 << endl;
    //cout << "block time 2: " << block_time_2 << endl;
    //cout << "write start time: " << write_start_time << endl;
    //cout << "write stream time 1: " << write_stream_time_1 << endl;
    //cout << "write stream time 1.0: " << write_stream_time_1_0 << endl;
    //cout << "write stream time 1.1: " << write_stream_time_1_1 << endl;
    //cout << "write stream time 1.2: " << write_stream_time_1_2 << endl; 
    
    //cout << "write stream time 2: " << write_stream_time_2 << endl;
    cout << "transfer time: " << transfer_time << endl;
    cout << "total time: " << total_time << endl;
    #endif
    //cout << "main time: " << main_time << endl;

    printf("%ld\n", ((main_end.tv_sec * 1000000 + main_end.tv_usec)
                      - (main_start.tv_sec * 1000000 + main_start.tv_usec)));


    //cout << "write time: " << write_time << endl;
    //cout << "buffer size: " << buffer.size() << "; " << _count << endl;   
    //
    
    pthread_mutex_destroy(&transfer_lock);
    pthread_cond_destroy(&transfer_cond);
    pthread_mutex_destroy(&prepare_lock);
    pthread_cond_destroy(&prepare_cond);
    pthread_mutex_destroy(&cap_lock);
    pthread_cond_destroy(&cap_cond);
    pthread_mutex_destroy(&process_lock);
    pthread_cond_destroy(&process_cond);


    return 0;
}

