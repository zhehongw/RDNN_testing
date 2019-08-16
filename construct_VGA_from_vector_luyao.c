#include <iostream>
#include <fstream>
#include <istream>
#include <sstream>
#include <vector>
#include <stdio.h>
#include <cmath>
#include<string>
#include "opencv/cv.h"
#include "opencv2/video/tracking.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include "opencv2/highgui/highgui.hpp"
#include "opencv2/core/core.hpp"
#include "colormap.hpp"
#include <bitset>

using namespace std;
using namespace cv;

const int bug_row = 0;
const int bug_col = 349;
const int overlap = 8;
int rowCounter = 0;
int colCounter = 0;
int row_shift = 0;
int col_shift = 0;
int image_num = 2;
int max_col = 18;

int row_num = 480;
int col_num = 752;

string line;
int addr = 0;
int last_addr = 0;
int disp;
int sub_row = 0;
int sub_col = 0;
string addr_bin;
string disp_bin;
int Min = 255;
int tmp = 0;

Mat median_filter (Mat& A, int kernel_size) {
    Mat result = A;
    int current = 0;
    int num = 0;
    uint8_t values[kernel_size*kernel_size];
    int half_window = (kernel_size - 1)/2;
    for (int row = 0; row < A.rows; row++) {
        for (int col = 0; col < A.cols; col++) {
            current = 0;
            num = 0;
            for (int count = 0; count < kernel_size*kernel_size; count++){
                values[count] = 255;
            }
            for (int row_w = -1 * half_window; row_w <= half_window; row_w++) {
                for (int col_w = -1 * half_window; col_w <= half_window; col_w++) {
                    if ((row + row_w < A.rows) && (col + col_w < A.cols) && (row + row_w >= 0) && (col + col_w >= 0)) {
                       
                        for (num = 0; num < kernel_size*kernel_size; num++){
              
                            if ((int)values[num] < (int)A.at<uint8_t>(row + row_w, col + col_w)) {       
                            }
                            else {
                                for (current = kernel_size*kernel_size - 1; current > num; current--) {
                                    values[current] = values[current-1];
                                }
                                values[num] = A.at<uint8_t>(row + row_w, col + col_w);
                                break;
                            }
                        }
                    }

                }
            }
            //find median
            uint8_t median = values[half_window * kernel_size + half_window];
            //set median
            if ((row + half_window < A.rows) && (col + half_window < A.cols) && (row - half_window >= 0) && (col - half_window >= 0)) {
                result.at<uint8_t>(row, col) = median;
            }
        }
    }
    return result;
}

int main () {
    cvNamedWindow("display");
    Mat dispMap = Mat::zeros(image_num * row_num, col_num, DataType<uint8_t>::type);
    Mat dispMap_medianfilter = Mat::zeros(image_num *row_num, col_num, DataType<uint8_t>::type);
    Mat sub_dispMap = Mat::zeros(50, 50, DataType<uint8_t>::type);

    for ( int row = 0; row < dispMap.rows; row++) {
        for (int col = 0; col < dispMap.cols; col++) {
            dispMap.at<uint8_t>(row, col) = (uint8_t)127;
        }
    }
    string line;
    ifstream result_file;
    result_file.open("streamIN_bin.txt", ios::binary | ios::in);
    if (result_file.is_open()){
	char line_char[4];
        while ( !result_file.eof() ){
	    result_file.read(line_char, sizeof(uint32_t));
            uint32_t line_bin =  (uint32_t)line_char[3] << 24 & 0xFF000000| 
                       	(uint32_t)line_char[2] << 16 & 0x00FF0000| 
                        (uint32_t)line_char[1] << 8 & 0x0000FF00| 
                        (uint32_t)line_char[0] & 0x000000FF;
	    line = bitset<32>(line_bin).to_string();
            string header = line.substr(1,6);
            if (header.compare("110101") == 0) {
                addr_bin = line.substr(7,12);
                const char* addr_cbin = addr_bin.c_str();
                unsigned long long addr = strtoll(addr_cbin, 0, 2);
                if(last_addr > 2490 && addr > 10 && addr < last_addr) {
                    Mat dispMap_left(dispMap, Range(0, row_num), Range::all());
                    Mat dispMap_right(dispMap, Range(row_num, 2*row_num), Range::all());
                    flip(dispMap_right, dispMap_right, 1);
                    Mat consistency = Mat::zeros(row_num, col_num, DataType<uint8_t>::type);
                    Mat dispMap_LRcheck = Mat::zeros(row_num, col_num, DataType<uint8_t>::type);
                    int LR_threshold = 4;
                    Mat dispMap_LR_check_scaled = Mat::zeros(dispMap_LRcheck.rows, dispMap_LRcheck.cols, DataType<uint8_t>::type);
                    Min = 255;
                    tmp = 0;
                    for(int row = 0; row < row_num; row++){
                        for(int col = 0; col < col_num; col++){
                            if(col - dispMap_left.at<uint8_t>(row, col) < col_num && col - dispMap_left.at<uint8_t>(row, col) >= 0){
                                consistency.at<uint8_t>(row, col) = (uint8_t)abs((dispMap_right.at<uint8_t>(row,col - (int)dispMap_left.at<uint8_t>(row,col)) - dispMap_left.at<uint8_t>(row,col)));
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
				if(dispMap_LRcheck.at<uint8_t>(row, col) != 0) {                              
                                tmp = dispMap_LRcheck.at<uint8_t>(row, col);
                            } else {                              
                                tmp = 1;
                            }
                            if(tmp < Min && tmp != 0){
                                Min = tmp;
                            }
                            tmp = (int) 16 * (tmp - Min);

                            if(0 < dispMap_LRcheck.at<uint8_t>(row, col) && dispMap_LRcheck.at<uint8_t>(row, col) < 255) { 
                                if(tmp < 255) {
                                    dispMap_LR_check_scaled.at<uint8_t>(row, col) = (uint8_t) 255 - tmp ;
                                } else {
                                    dispMap_LR_check_scaled.at<uint8_t>(row, col) = (uint8_t) 255 - 254 ;
                                }
                            } else if(dispMap_LRcheck.at<uint8_t>(row, col) == 255){
                                dispMap_LR_check_scaled.at<uint8_t>(row, col) = 255;
                            } else if(dispMap_LRcheck.at<uint8_t>(row, col) == 0){
                                dispMap_LR_check_scaled.at<uint8_t>(row, col) = 255;
                            } else {
                                dispMap_LR_check_scaled.at<uint8_t>(row, col) = 255;
                            }
			    dispMap.at<uint8_t>(row, col) = (uint8_t)127;
                        }
                    }

                    //dispMap_medianfilter = median_filter(dispMap_LR_check_scaled, 5);
		    medianBlur(dispMap_LR_check_scaled,dispMap_medianfilter,5);
                    applyColorMap(dispMap_medianfilter, dispMap_medianfilter, COLORMAP_RAINBOW);
                    dispMap_medianfilter.convertTo(dispMap_medianfilter, CV_8UC3, 255.0);
  
		    imshow("display",dispMap_medianfilter);//dispMap_medianfilter
		    char c = cvWaitKey(30);
		   
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
                disp_bin = line.substr(20,7); 
                const char* disp_cbin = disp_bin.c_str();
                unsigned long long disp = strtoll(disp_cbin, 0, 2);
                uint8_t disp_result = uint8_t(disp);

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
                
                    if(int(disp_result) >= 128) {
                        dispMap.at<uint8_t>(sub_row + row_shift, sub_col + col_shift) = uint8_t(255);
                        sub_dispMap.at<uint8_t>(sub_row, sub_col) = uint8_t(255);
                    } else {
                        dispMap.at<uint8_t>(sub_row + row_shift, sub_col + col_shift) = uint8_t(disp_result);
                        sub_dispMap.at<uint8_t>(sub_row, sub_col) = uint8_t(disp_result);

                    }
                    if ( addr - last_addr < 8 ) {
                        for(int loop = 0; loop < addr - last_addr; loop++) {
                            dispMap.at<uint8_t>(sub_row + row_shift, sub_col + col_shift - loop) = uint8_t(disp_result);
                            sub_dispMap.at<uint8_t>(sub_row, sub_col - loop) = uint8_t(disp_result);
                        }
                    }
                }
                if(addr < last_addr && last_addr > 2480) {
                    colCounter++;
                    if(colCounter == max_col) {
                        rowCounter++;
                        colCounter = 0;
                    }
                }
                last_addr = addr;
            } 
        }
    }
    result_file.close();
     
    dispMap.release(); 
    dispMap_medianfilter.release();
    sub_dispMap.release();
    cvDestroyWindow("display");
    return 0;
}
