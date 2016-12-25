#include <iostream>
#include <fstream>
#include <istream>
#include <sstream>
#include <vector>
#include <stdio.h>
#include <cmath>
#include<string>
//
#include "opencv/cv.h"
//#include "cxcore.h"
//#include "highgui.h"
#include "opencv2/video/tracking.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include "opencv2/highgui/highgui.hpp"
//#include "opencv2/contrib/contrib.hpp"
#include "opencv2/core/core.hpp"
#include "colormap.hpp"
#include <bitset>


using namespace std;
using namespace cv;

//#define DEBUG  
const int bug_row = 0;
const int bug_col = 349;

void save_image(const string filename, const Mat& src, int colormap) {
    Mat cm_dst;
    applyColorMap(src, cm_dst, colormap);
    cm_dst.convertTo(cm_dst, CV_8UC3, 255.0);
    imwrite(filename, cm_dst);
}

string type2str(int type) {
    string r;
    uchar depth = type & CV_MAT_DEPTH_MASK;
    uchar chans = 1 + (type >> CV_CN_SHIFT);
    switch ( depth ) {
        case CV_8U:  r = "8U"; break;
        case CV_8S:  r = "8S"; break;
        case CV_16U: r = "16U"; break;
        case CV_16S: r = "16S"; break;
        case CV_32S: r = "32S"; break;
        case CV_32F: r = "32F"; break;
        case CV_64F: r = "64F"; break;
        default:     r = "User"; break;
    }
    r += "C";
    r += (chans+'0');

    return r;
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
    for (int row = 0; row < Ground_truth.rows; row++){
        for (int col = 128; col < Ground_truth.cols; col++){
            if(Ground_truth.at<uint8_t>(row, col) != 0 && Ground_truth.at<uint8_t>(row, col) < 128){
                    //&& disparity.at<uint8_t>(row, col) != 0) {
                //cout << "row: " << row << ", col: " << col << endl;
                //cout << "gt: " << (int)Ground_truth.at<uint8_t>(row, col) << endl;
                //cout << "disp: " << (int)disparity.at<uint8_t>(row, col) << endl;

                //if((int)Confidence.at<uint8_t>(row, col) > 6){
                    //cout << "difference: " << difference << endl;
                    int difference = (int)disparity.at<uint8_t>(row, col) - (int)Ground_truth.at<uint8_t>(row, col);
                    if(difference >= 0) {
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
                //}
                num++;
            }    
        }
    }
    error = error/(float)valid_num;
    confident_error = confident_error/(float)confident_valid_num;
    outliners = (float)error_num/(float)valid_num;
    confident_outliners = (float)confident_error_num/(float)confident_valid_num;
    cout << "total: " << num << ", valid_num: " << valid_num << ", error_num: " << error_num << ", outliners: " << outliners << ", average error: " << error << endl; 
    //cout << "confident: total: " << num << ", valid_num: " << confident_valid_num << ", error_num: " << confident_error_num << ", outliners: " << confident_outliners << ", average error: " << confident_error << endl; 
    
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
                //if((int)Confidence.at<uint8_t>(row, col) > 6){
                //cout << "difference: " << difference << endl;
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
    //outliners = (float)error_num/(float)valid_num;
    cout << "total: " << num << ", valid_num: " << valid_num << ", avg_dist_error: " << error_counter << endl; 
    return;
}
      

Mat median_filter (Mat& A, int kernel_size) {
    Mat result = A;
    uint8_t max = 0;
    int max_row = 0;
    int max_col = 0;
    int current = 0;
    int num = 0;
    uint8_t values[kernel_size*kernel_size];
    Mat patch = Mat::zeros(kernel_size, kernel_size, DataType<uint8_t>::type);
    int half_window = (kernel_size - 1)/2;
    for (int row = 0; row < A.rows; row++) {
        for (int col = 0; col < A.cols; col++) {
            //cout << "processing : " << row << ", " << col << endl;
            //reset
            max = 0;
            max_row = 0;
            max_col = 0;
            current = 0;
            num = 0;
            for (int count = 0; count < kernel_size*kernel_size; count++){
                values[count] = 255;
            }


            for (int row_w = -1 * half_window; row_w <= half_window; row_w++) {
                for (int col_w = -1 * half_window; col_w <= half_window; col_w++) {
                    if ((row + row_w < A.rows) && (col + col_w < A.cols) && (row + row_w >= 0) && (col + col_w >= 0)) {
                        //cout << "In window processing : " << row + row_w << ", " << col + col_w << endl;
                        //values[(row_w + half_window) * kernel_size + col_w + half_window] = A.at<uint8_t>(row + row_w, col + col_w);
                        /*
                        //cout << "sort: ";
                        for ( int i = 0; i < kernel_size*kernel_size; i++) {
                            cout << (int)values[i] << ", ";
                        }
                        cout << endl;
                        */
                        if (A.at<uint8_t>(row + row_w, col + col_w) > max) { 
                            max = A.at<uint8_t>(row + row_w, col + col_w);
                            max_row = row + row_w;
                            max_col = col + col_w;
                        }
                        for (num = 0; num < kernel_size*kernel_size; num++){
                            //cout << "values[" << num << "] = " << (int)values[num] << ", (" << row + row_w << ", " << col + col_w << ") = " << 
                            //(int)A.at<uint8_t>(row + row_w, col + col_w) << endl;
                            if ((int)values[num] < (int)A.at<uint8_t>(row + row_w, col + col_w)) {
                                //cout << "jump over" << endl;        
                            }
                            else {
                                //cout << "position: " << num << endl;
                                for (current = kernel_size*kernel_size - 1; current > num; current--) {
                                    values[current] = values[current-1];
                                }
                                //tmp = values[num];
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
                /*
                if (row == 2 && col == 2) {
                    cout << "row - half_window: " << col - half_window << ", " << col + half_window + 1 <<  endl;
                    //patch = A.colRange(row - half_window, row + half_window + 1).rowRange(col - half_window, col + half_window + 1);
                    //patch = A(Range(row - half_window, row + half_window + 1), Range(col - half_window, col + half_window + 1));
                    for (int r = -1 * half_window; r <= half_window; r++) {
                        for (int c = -1 * half_window; c <= half_window; c++) {
                            patch.at<uint8_t>(r + half_window, c + half_window) = A.at<uint8_t>(row + r, col + c);
                        }
                    }
                    cout << "patch: " << endl;
                    cout << patch << endl;


                    cout << "sort: ";
                    for ( int i = 0; i < kernel_size*kernel_size; i++) {
                        cout << (int)values[i] << ", ";
                    }
                    cout << endl;
                    cout << "replacing: " << "[" << max_row << ", " << max_col << "]" << " with " << (int)median << endl;
                }
                */
                //result.at<uint8_t>(max_row, max_col) = median;
                //if (max_row == row && max_col == col) {
                result.at<uint8_t>(row, col) = median;
                //cout << "replacing: " << "[" << max_row << ", " << max_col << "]" << " with " << (int)median << endl;
                //}
            }
        }
    }

    return result;
}

int main () {
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


    Mat left_gray, right_gray; 
    char GT_dispMap_string[1024];
    if(frameCounter < 10) {
        sprintf(frameCounter_string, "00000000%d", frameCounter);
    } else if (frameCounter >= 10 && frameCounter < 100){
        sprintf(frameCounter_string, "0000000%d", frameCounter);
    } else {
        sprintf(frameCounter_string, "000000%d", frameCounter);
    }

    sprintf(GT_dispMap_string, "../../6D_vision/datasets/stixel/goodWeather/2010-09-02_092748/images/img_c0_%s.pgm", frameCounter_string);

    char dispMap_string[1024];
    char dispMap_median_filter_string[1024];
    char dispMap_median_filter_LR_check_string[1024];
    char dispMap_LR_check_color_string[1024];
    char dispMap_left_string[1024];
    char dispMap_right_string[1024];
 
    int Max = 0;
    int Max_2 = 0;
    int Min = 255;
    int Min_2 = 0;

    int tmp = 0;
    int MAX_VALUE = 230000;
    int line_cnt = 0;

    //sprintf(dispMap_string, "KITTI_test_cases/testbench/images/dispMap_%s.png", frameCounter_string);
           
    //char dispMap_medianfilter_string[1024];
    //sprintf(dispMap_medianfilter_string, "KITTI_test_cases/testbench/images/dispMap_with_median_filter_%s.png", frameCounter_string);


    //Mat Ground_truth = imread(GT_dispMap_string, CV_LOAD_IMAGE_GRAYSCALE);
    
    Mat Ground_truth = Mat::zeros(row_num, col_num, DataType<uint8_t>::type);
    
    Mat dispMap = Mat::zeros(image_num * Ground_truth.rows, Ground_truth.cols, DataType<uint8_t>::type);
    Mat dispMap_medianfilter = Mat::zeros(image_num *Ground_truth.rows, Ground_truth.cols, DataType<uint8_t>::type);
    Mat dispMap_refill_medianfilter = Mat::zeros(image_num*Ground_truth.rows, Ground_truth.cols, DataType<uint8_t>::type);
    Mat dispMap_refill = Mat::zeros(image_num*Ground_truth.rows, Ground_truth.cols, DataType<uint8_t>::type);
    Mat conf_Map = Mat::zeros(image_num*Ground_truth.rows, Ground_truth.cols, DataType<uint8_t>::type);
    Mat dispMap_error = Mat::zeros(image_num*Ground_truth.rows, Ground_truth.cols, DataType<uint8_t>::type);
    Mat sub_confidence = Mat::zeros(50, 50, DataType<uint8_t>::type);
    //Mat sub_consistency = Mat::zeros(50, 50, DataType<uint8_t>::type);
    Mat sub_dispMap = Mat::zeros(50, 50, DataType<uint8_t>::type);


    //CvMat *Q = (CvMat *)cvLoad("stereo_camera_calibrate/Q.xml",NULL,NULL,NULL);
    //CvMat *mx10 = (CvMat *)cvLoad("stereo_camera_calibrate/mx1.xml",NULL,NULL,NULL);
    //CvMat *my10 = (CvMat *)cvLoad("stereo_camera_calibrate/my1.xml",NULL,NULL,NULL);
    //CvMat *mx20 = (CvMat *)cvLoad("stereo_camera_calibrate/mx2.xml",NULL,NULL,NULL);
    //CvMat *my20 = (CvMat *)cvLoad("stereo_camera_calibrate/my2.xml",NULL,NULL,NULL);
    //Mat mx1 = cv::Mat(mx10, true); 
    //Mat my1 = cv::Mat(my10, true); 
    //Mat mx2 = cv::Mat(mx20, true); 
    //Mat my2 = cv::Mat(my20, true); 
    //Mat left_img = imread("left_small.png",CV_LOAD_IMAGE_COLOR);
    //Mat right_img = imread("right_small.png",CV_LOAD_IMAGE_COLOR);
    string line;
    int addr = 0;
    int last_addr = 0;
    int disp;
    int sub_row = 0;
    int sub_col = 0;
    //cout << "row_shift: " << row_shift << endl;
    //cout << "col_shift: " << col_shift << endl;
    //sprintf(result_file_string, "KITTI_test_cases/testbench/outputs/result_mem_%s_row_%d_col_%d.mem", 
    //                            frameCounter_string, 
    //                            rowCounter, 
    //                            colCounter);
    //cout << "reading: " << result_file_string << endl;
    string addr_bin;
    string disp_bin;
    string conf_bin;


    for ( int row = 0; row < dispMap.rows; row++) {
        for (int col = 0; col < dispMap.cols; col++) {
            dispMap.at<uint8_t>(row, col) = (uint8_t)127;
        }
    }



    VideoWriter out_capture("images_JPL/depth_video.avi", CV_FOURCC('M','J','P','G'), 30, Size(752,480));

    //ifstream result_file( "output_datastream/stixel/image_000979.txt");
    //ifstream result_file( "image_000975.txt");
    ifstream result_file;
    result_file.open("streamIN_bin.txt", ios::binary | ios::in);
    if (result_file.is_open()){
        //cout << "reading success" << endl;
	char line_char[4];
        //while ( result_file >> line){
        while ( !result_file.eof() ){
	    result_file.read(line_char, sizeof(uint32_t));
            uint32_t line_bin =  (uint32_t)line_char[3] << 24 & 0xFF000000| 
                       	(uint32_t)line_char[2] << 16 & 0x00FF0000| 
                        (uint32_t)line_char[1] << 8 & 0x0000FF00| 
                        (uint32_t)line_char[0] & 0x000000FF;
	    line = bitset<32>(line_bin).to_string();
            //cout << "line string: " << line << endl;;
            line_cnt++;
            string header = line.substr(1,6);
            //cout << "header string: " << header << endl;;
            if (header.compare("110101") == 0) {

            //cout << disp_result << endl;
                addr_bin = line.substr(7,12);
                const char* addr_cbin = addr_bin.c_str();
                //cout << "addr string: " << addr_cbin << endl;;
                unsigned long long addr = strtoll(addr_cbin, 0, 2);

                /*
                if(addr - last_addr != 1) {
                    cout << "addr: " << addr << endl;;
                    cout << "last addr: " << last_addr << endl;

                }
                */

                if(last_addr > 2490 && addr > 10 && addr < last_addr) {
                    //last frame is done
                    if(frameCounter < 10) {
                        sprintf(frameCounter_string, "00000000%d", frameCounter);
                    } else if (frameCounter >= 10 && frameCounter < 100){
                        sprintf(frameCounter_string, "0000000%d", frameCounter);
                    } else {
                        sprintf(frameCounter_string, "000000%d", frameCounter);
                    }
                    sprintf(dispMap_string, "images_JPL/dispMap_%s.png", frameCounter_string);
                    sprintf(dispMap_left_string, "images_JPL/dispMap_left_%s.png", frameCounter_string);
                    sprintf(dispMap_right_string, "images_JPL/dispMap_right_%s.png", frameCounter_string);
                    sprintf(dispMap_median_filter_string, "images_JPL/dispMap_median_filter_%s.png", frameCounter_string);
                    sprintf(dispMap_median_filter_LR_check_string, "images_JPL/dispMap_median_filter_LR_check_%s.png", frameCounter_string);
                    sprintf(dispMap_LR_check_color_string, "images_JPL/dispMap_LR_check_color_%s.png", frameCounter_string);

                    Mat dispMap_left(dispMap, Range(0, row_num), Range::all());
                    Mat dispMap_right_flip(dispMap, Range(row_num, 2*row_num), Range::all());

                    Mat dispMap_right;
                    flip(dispMap_right_flip, dispMap_right, 1);

                    //dispMap_medianfilter = median_filter(dispMap, 7);

                    
                    Mat consistency = Mat::zeros(row_num, col_num, DataType<uint8_t>::type);
                    Mat dispMap_LRcheck = Mat::zeros(row_num, col_num, DataType<uint8_t>::type);


                    Mat dispMap_left_copied = dispMap_left.clone();
                    Mat dispMap_right_copied = dispMap_right.clone();
                    //dispMap_left_copied = median_filter(dispMap_left_copied, 5);
                    //dispMap_right_copied = median_filter(dispMap_right_copied, 5);

                    for(int row = 0; row < row_num; row++){
                        for(int col = 0; col < col_num; col++){
                            if(col - dispMap_left_copied.at<uint8_t>(row, col) < col_num && col - dispMap_left_copied.at<uint8_t>(row, col) >= 0){
                                consistency.at<uint8_t>(row, col) = (uint8_t)abs((dispMap_right_copied.at<uint8_t>(row,col - (int)dispMap_left_copied.at<uint8_t>(row,col)) - dispMap_left_copied.at<uint8_t>(row,col)));
                            }
                            else{
                                consistency.at<uint8_t>(row, col) = 255;
                            }
                        }
                    }

                    int LR_threshold = 4;
                    for(int row = 0; row < row_num; row++){
                        for(int col = 0; col < col_num; col++){
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
                 
                    Max = 0;
                    Max_2 = 0;
                    Min = 255;
                    Min_2 = 0;
                    tmp = 0;
                    MAX_VALUE = 230000;
                    for(int row = 0; row < dispMap_LRcheck.rows; row++){
                        for(int col = 0; col < dispMap_LRcheck.cols; col++){

                            if(dispMap_LRcheck.at<uint8_t>(row, col) != 0) {
                                //tmp = MAX_VALUE/img1.at<uint16_t>(row, col);
                                tmp = dispMap_LRcheck.at<uint8_t>(row, col);
                            } else {
                                //tmp = MAX_VALUE + 1;
                                tmp = 1;
                            }

                            if(tmp > Max){
                                Max = tmp;
                            }

                            //if(tmp > Max_2 && tmp != MAX_VALUE + 1 ){
                            if(tmp > Max_2 && tmp != MAX_VALUE + 1 && tmp != 255 ){
                                Max_2 = tmp;
                            }

                            if(tmp < Min && tmp != 0){
                                Min = tmp;
                            }

                            tmp = (int) 16 * (tmp - Min);
                            //tmp = 8*tmp;
                      

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

                    //imwrite( "scaled.png", dispMap_LR_check_scaled);                         
                    //cout << (int)Max << std::endl;
                    //cout << (int)Max_2 << std::endl;
                    //cout << (int)Min << std::endl;

                    dispMap_medianfilter = median_filter(dispMap_LR_check_scaled, 5);

                    applyColorMap(dispMap_medianfilter, dispMap_LR_check_color, COLORMAP_RAINBOW);
                    dispMap_LR_check_color.convertTo(dispMap_LR_check_color, CV_8UC3, 255.0);
                    //save_image(dispMap_LR_check_color_string, dispMap_LR_check_color, COLORMAP_RAINBOW);
                    //imwrite(dispMap_LR_check_color_string, dispMap_LR_check_color);
                    out_capture.write(dispMap_LR_check_color);

                    //write to video
                    


                    //dispMap_medianfilter = median_filter(dispMap, 3);
                    //applyColorMap(dispMap_medianfilter, dispMap_color, COLORMAP_RAINBOW);
                    //save_image(dispMap_string, dispMap_color, COLORMAP_RAINBOW);




                    //imwrite( dispMap_string, dispMap);                         
                    //imwrite( dispMap_left_string, dispMap_left);
                    //imwrite( dispMap_right_string, dispMap_right);
                    //imwrite( dispMap_median_filter_string, dispMap_medianfilter);
                    //imwrite( dispMap_median_filter_LR_check_string, dispMap_LRcheck);



                 
                    //cout << "addr: " << addr << endl;;
                    //cout << "last addr: " << last_addr << endl;
                    //cout << "line: " << line_cnt << endl;
                    //cout << "new frame: " << endl;
                    //cout << "row counter: " << rowCounter << endl;
                    //cout << "col counter: " << colCounter << endl;

                    frameCounter++;
                    //clean disp map
                    for ( int row = 0; row < dispMap.rows; row++) {
                        for (int col = 0; col < dispMap.cols; col++) {
                            dispMap.at<uint8_t>(row, col) = (uint8_t)127;
                        }
                    }
                    sub_row = 0;
                    sub_col = 0;
                    rowCounter = 0;
                    colCounter = 0;
                    row_shift = 0;
                    col_shift = 0;
                    last_addr = 0;

                }

                //sub_dispMap.at<uint8_t>(sub_row, sub_col) = uint8_t(disp_result);
                disp_bin = line.substr(20,7); 
                const char* disp_cbin = disp_bin.c_str();

                conf_bin = line.substr(29,3); 
                const char* conf_cbin = conf_bin.c_str();
                unsigned long long conf = strtoll(conf_cbin, 0, 2);
                //cout << "conf string: " << conf_cbin << endl;;

                unsigned long long disp = strtoll(disp_cbin, 0, 2);

                uint8_t disp_result = uint8_t(disp);
                //cout << "disp: " << int(disp_result) << endl;;

                col_shift = colCounter * (50 - overlap);
                row_shift = rowCounter * (50 - overlap);
                sub_row = int(addr/50);
                sub_col = int(addr%50);
                //cout << "sub_row: " << sub_row << ", sub_col: " << sub_col << endl;
                if( sub_col < (50 - overlap/2) && 
                    sub_row < (50 - overlap/2) &&
                    sub_col >= (overlap/2) &&
                    sub_row >= (overlap/2) &&
                    sub_row + row_shift < image_num * Ground_truth.rows && 
                    sub_col + col_shift < Ground_truth.cols){

                    //conf_Map.at<uint8_t>(sub_row + row_shift, sub_col + col_shift) = uint8_t(conf * 16);
                    if(int(disp_result) >= 128) {
                        //dispMap.at<uint8_t>(sub_row + row_shift, sub_col + col_shift) = uint8_t(disp_result);
                        dispMap.at<uint8_t>(sub_row + row_shift, sub_col + col_shift) = uint8_t(255);
                        sub_dispMap.at<uint8_t>(sub_row, sub_col) = uint8_t(255);
                    } else {
                        dispMap.at<uint8_t>(sub_row + row_shift, sub_col + col_shift) = uint8_t(disp_result);
                        sub_dispMap.at<uint8_t>(sub_row, sub_col) = uint8_t(disp_result);
                        //cout << "disp string: " << disp_cbin << endl;;
                        //cout << "with pixel: " << sub_row << ", " << sub_col << ", value: " << int(disp_result) << endl;

                    }
                    if ( addr - last_addr < 8 ) {
                        for(int loop = 0; loop < addr - last_addr; loop++) {
                            dispMap.at<uint8_t>(sub_row + row_shift, sub_col + col_shift - loop) = uint8_t(disp_result);
                            sub_dispMap.at<uint8_t>(sub_row, sub_col - loop) = uint8_t(disp_result);
                        }
                    }
                    //cout << "filling pixel: \t" << sub_row + row_shift << ", \t" << sub_col + col_shift << 
                    //    " \twith pixel: " << sub_row << ", \t" << sub_col << ", value: \t" << int(disp_result) << endl;
                }

                if(addr < last_addr && last_addr > 2480) {
                    //cout << "new block" << endl;
                    colCounter++;
                    if(colCounter == max_col) {
                        rowCounter++;
                        colCounter = 0;
                    }
                }
                last_addr = addr;
            } else {
                //break;
            }
        }
    }
    result_file.close();

    return 0;
}
