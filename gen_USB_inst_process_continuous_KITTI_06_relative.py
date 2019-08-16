import os
from numpy import arange
import bisect
from decimal import *
import numpy
import math
from scipy import stats as scistats
import csv
from scipy.ndimage.filters import correlate as convolveim
import copy
import scipy
from numpy.linalg import inv
import cv2

def bindigits(n, bits):
    s = bin(n & int("1"*bits, 2))[2:]
    return ("{0:0>%s}" % (bits)).format(s)

def add_junk(USB_inst_file):
    for dummy in range(0, 32):
        USB_inst_file.write('00' + '000000' + '000000000000000000000000' + '\n') 
        #USB_inst_file.write('11' + '001100' + '000000000001000000000000' + '\n') #L2_THRESHOLD
        #USB_inst_file.write('11' + '000010' + '000000000000000101110010' + '\n') #image height
    return

def read_GT_pose(GT_pose_file_string):

    GT_RMat_double = numpy.zeros((2000, 3, 3), dtype=numpy.float) 
    GT_TMat_double = numpy.zeros((2000, 3), dtype=numpy.float) 

    img_cnt = 0
    with open(GT_pose_file_string) as GT_pose_file:
        for line in GT_pose_file:
            split_line = line.replace('\n', ' ').split(" ")
            #print split_line
            GT_RMat_double[img_cnt, 0, 0] = float(split_line[0])
            GT_RMat_double[img_cnt, 0, 1] = float(split_line[1])
            GT_RMat_double[img_cnt, 0, 2] = float(split_line[2])
            GT_RMat_double[img_cnt, 1, 0] = float(split_line[4])
            GT_RMat_double[img_cnt, 1, 1] = float(split_line[5])
            GT_RMat_double[img_cnt, 1, 2] = float(split_line[6])
            GT_RMat_double[img_cnt, 2, 0] = float(split_line[8])
            GT_RMat_double[img_cnt, 2, 1] = float(split_line[9])
            GT_RMat_double[img_cnt, 2, 2] = float(split_line[10])

            GT_TMat_double[img_cnt, 0] = float(split_line[3])
            GT_TMat_double[img_cnt, 1] = float(split_line[7])
            GT_TMat_double[img_cnt, 2] = float(split_line[11])

            img_cnt = img_cnt + 1

            #print GT_RMat_double[img_cnt]
            #print GT_TMat_double[img_cnt]

    GT_pose_file.close()

    return GT_RMat_double, GT_TMat_double

def write_image_block(image_block, block_size, USB_inst_file, odd_0_even_1):
    image_word_cnt = 0
    image_word = ''
    SLAM_image_mem_cnt = 0
    for row in range (0, block_size):
        for col in range (0, block_size):
            image_word = str(bindigits(image_block[row][col], 8)) + str(image_word)
            image_word_cnt = image_word_cnt + 1
            if(image_word_cnt == 8):
                image_word_reverse = image_word[::-1]
                #write control 0
                if(odd_0_even_1 == 0):
                    USB_inst_file.write('11' + '000000' + '110' + '010' + bindigits(3, 2) + bindigits(SLAM_image_mem_cnt, 16) + '\n') 
                else:
                    USB_inst_file.write('11' + '000000' + '110' + '010' + bindigits(3, 2) + bindigits(SLAM_image_mem_cnt + 2048, 16) + '\n') 

                for i in range(0, 3):
                    if(i < 2): 
                        USB_inst_file.write('10' + str(image_word_reverse[i*30:i*30+30][::-1]) + '\n') 
                    else:
                        USB_inst_file.write('10' + '0'*26 + str(image_word_reverse[i*30:i*30+4][::-1]) + '\n') 
                image_word = ''
                image_word_cnt = 0
                SLAM_image_mem_cnt = SLAM_image_mem_cnt + 1

def write_depth_block(depth_block, block_size, USB_inst_file, odd_0_even_1):
    write_depth_mem_num = 0
    SLAM_depth_mem_cnt = 0
    depth_word = ''

    USB_inst_file.write('11' + '000000' + '110' + '011' + bindigits(16383, 18) + '\n') 
    for row in range (0, block_size):
        for col in range (0, block_size):
            #print depth_word 
            depth_word = str(bindigits(depth_block[row][col], 8))
            depth_word_reverse = depth_word[::-1]
            #write control 0
            USB_inst_file.write('10' + bindigits(SLAM_depth_mem_cnt, 18) + 4*'0' + str(depth_word_reverse[0:8][::-1]) + '\n') 
            SLAM_depth_mem_cnt = SLAM_depth_mem_cnt + 1

def copy_img_block(image, block_row_cnt, block_col_cnt, image_height, image_width):
    image_block = numpy.zeros((128, 128), dtype=numpy.int)
    for row in range(0, 128):
        for col in range(0, 128):
            if(block_row_cnt*96+row < image_height and 64+block_col_cnt*96+col < image_width):
                image_block[row, col] = image[block_row_cnt*96+row, 64+block_col_cnt*96+col]
    image_block -= 128
    return image_block

def copy_depth_block(image, block_row_cnt, block_col_cnt, image_height, image_width):
    image_block = numpy.zeros((128, 128), dtype=numpy.int)
    for row in range(0, 128):
        for col in range(0, 128):
            if(block_row_cnt*96+row < image_height and 64+block_col_cnt*96+col < image_width):
                image_block[row, col] = image[block_row_cnt*96+row, 64+block_col_cnt*96+col]
    return image_block

def initialize(USB_inst_file):
    CNN_icache_file = open('CNN_icache' + '.txt','w+')
    CNN_icache_cnt = 0 
    with open("DoG_inst.txt") as DoG_icache_file:
        for line in DoG_icache_file:
            line = line[:-1]
            inst_word = '{message:>384{fill}}'.format(message=line, fill='').replace(' ', '0')
            #write control 0
            USB_inst_file.write('11' + '000000' + '110' + '000' + bindigits(12, 4) + bindigits(CNN_icache_cnt, 14) + '\n') #KEYPOINT_THRESHOLD
            line_reverse = line[::-1]
            #print line_reverse
            for i in range(0, 12):
                if(i < 11): 
                    USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
                else:
                    USB_inst_file.write('10' + '0'*18 + str(line_reverse[i*30:i*30+12][::-1]) + '\n') 
            CNN_icache_cnt = CNN_icache_cnt + 1

    DoG_icache_file.close()

    with open("Ext_inst.txt") as Ext_icache_file:
        for line in Ext_icache_file:
            line = line[:-1]
            inst_word = '{message:>384{fill}}'.format(message=line, fill='').replace(' ', '0')
            #write control 0
            USB_inst_file.write('11' + '000000' + '110' + '000' + bindigits(12, 4) + bindigits(CNN_icache_cnt, 14) + '\n') #KEYPOINT_THRESHOLD
            line_reverse = line[::-1]
            #print line_reverse
            for i in range(0, 12):
                if(i < 11): 
                    USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
                else:
                    USB_inst_file.write('10' + '0'*18 + str(line_reverse[i*30:i*30+12][::-1]) + '\n') 
            CNN_icache_cnt = CNN_icache_cnt + 1

    Ext_icache_file.close()

    CNN_wram_file = open('CNN_wram' + '.txt','w+')
    CNN_wram_cnt = 0 

    with open("DoG_WRAM_full.mem") as DoG_wram_file:
        for line in DoG_wram_file:
            line = line[:-1]
            inst_word = '{message:>512{fill}}'.format(message=line, fill='').replace(' ', '0')
            #write control 0
            USB_inst_file.write('11' + '000000' + '110' + '001' + bindigits(18, 5) + bindigits(CNN_wram_cnt, 13) + '\n') 
            line_reverse = line[::-1]
            #print line_reverse
            for i in range(0, 18):
                if(i < 17): 
                    USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
                else:
                    USB_inst_file.write('10' + '0'*28 + str(line_reverse[i*30:i*30+2][::-1]) + '\n') 
            CNN_wram_cnt = CNN_wram_cnt + 1

    DoG_wram_file.close()

    with open("Ext_WRAM_full.mem") as Ext_wram_file:
        for line in Ext_wram_file:
            line = line[:-1]
            inst_word = '{message:>512{fill}}'.format(message=line, fill='').replace(' ', '0')
            #write control 0
            USB_inst_file.write('11' + '000000' + '110' + '001' + bindigits(18, 5) + bindigits(CNN_wram_cnt, 13) + '\n') 
            line_reverse = line[::-1]
            #print line_reverse
            for i in range(0, 18):
                if(i < 17): 
                    USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
                else:
                    USB_inst_file.write('10' + '0'*28 + str(line_reverse[i*30:i*30+2][::-1]) + '\n') 
            CNN_wram_cnt = CNN_wram_cnt + 1

    Ext_wram_file.close()

    CNN_bram_file = open('CNN_bram' + '.txt','w+')
    CNN_bram_cnt = 0 

    with open("DoG_BRAM_full.mem") as DoG_bram_file:
        for line in DoG_bram_file:
            line = line[:-1]
            inst_word = '{message:>64{fill}}'.format(message=line, fill='').replace(' ', '0')
            #write control 0
            USB_inst_file.write('11' + '000000' + '110' + '100' + bindigits(3, 2) + bindigits(CNN_bram_cnt, 16) + '\n') 
            line_reverse = line[::-1]
            #print line_reverse
            for i in range(0, 3):
                if(i < 2): 
                    USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
                else:
                    USB_inst_file.write('10' + '0'*26 + str(line_reverse[i*30:i*30+4][::-1]) + '\n') 
            CNN_bram_cnt = CNN_bram_cnt + 1

    DoG_bram_file.close()

    with open("Ext_BRAM_full.mem") as Ext_bram_file:
        for line in Ext_bram_file:
            line = line[:-1]
            inst_word = '{message:>64{fill}}'.format(message=line, fill='').replace(' ', '0')
            #write control 0
            USB_inst_file.write('11' + '000000' + '110' + '100' + bindigits(3, 2) + bindigits(CNN_bram_cnt, 16) + '\n') 
            line_reverse = line[::-1]
            #print line_reverse
            for i in range(0, 3):
                if(i < 2): 
                    USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
                else:
                    USB_inst_file.write('10' + '0'*26 + str(line_reverse[i*30:i*30+4][::-1]) + '\n') 
            CNN_bram_cnt = CNN_bram_cnt + 1

    Ext_bram_file.close()
    return

def write_abs_pose_est_t0(GT_RMat_double, GT_TMat_double, frame_cnt):

    RMat_double = numpy.zeros((3, 3), dtype=numpy.float) 
    cv2.transpose(GT_RMat_double[frame_cnt], RMat_double)

    RVec_double = numpy.zeros((3), dtype=numpy.float) 
    #cv2.Rodrigues(RVec_double, RMat_double[frame_cnt])
    cv2.Rodrigues(RMat_double, RVec_double)

    TVec_double = numpy.zeros((3), dtype=numpy.float) 
    #print GT_RMat_double[frame_cnt]
    #print GT_TMat_double[frame_cnt]
    TVec_double = -1.0 * inv(GT_RMat_double[frame_cnt]).dot(GT_TMat_double[frame_cnt])

    #print RMat_double
    #print RVec_double
    #print TVec_double

    RMat_int= numpy.zeros((3, 3), dtype=numpy.int) 
    RVec_int= numpy.zeros((3), dtype=numpy.int) 
    TVec_int= numpy.zeros((3), dtype=numpy.int) 

    RMat_int = (RMat_double * 1024.0 * 1024.0 * 512.0).astype(int)
    RVec_int = (RVec_double * 1024.0 * 1024.0 * 1024.0 * 2.0).astype(int)
    TVec_int = (TVec_double * 1024.0 * 1024.0).astype(int)

    #print RMat_int
    #print RVec_int
    #print TVec_int

    #RMat
    for row in range(0,3):
        for col in range(0,3):
            #print bindigits(RMat_int[row, col],32)
            USB_inst_file.write('11' + '010100' + bindigits(row,2) + bindigits(col,2) + '0' + '0' + '00' + bindigits(RMat_int[row, col],32)[-16:] + '\n') 
            #print('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '0' + '0' + '00' + bindigits(RMat_int[row, col],32)[-16:]) 
            if(row == 2 and col == 2):
                USB_inst_file.write('11' + '010100' + bindigits(row,2) + bindigits(col,2) + '1' + '1' + '00' + bindigits(RMat_int[row, col],32)[0:-16] + '\n') 
                #print('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '1' + '1' + '00' + bindigits(RMat_int[row, col],32)[0:-16]) 
            else:
                USB_inst_file.write('11' + '010100' + bindigits(row,2) + bindigits(col,2) + '1' + '0' + '00' + bindigits(RMat_int[row, col],32)[0:-16] + '\n') 
                #print('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '1' + '0' + '00' + bindigits(RMat_int[row, col],32)[0:-16]) 
    #TMat
    for row in range(0,3):
        USB_inst_file.write('11' + '010101' + bindigits(row,2) + bindigits(0,2) + '0' + '0' + bindigits(TVec_int[row],36)[-18:] + '\n') 
        if(row == 2):
            USB_inst_file.write('11' + '010101' + bindigits(row,2) + bindigits(0,2) + '1' + '1' + bindigits(TVec_int[row],36)[0:-18] + '\n') 
        else:
            USB_inst_file.write('11' + '010101' + bindigits(row,2) + bindigits(0,2) + '1' + '0' + bindigits(TVec_int[row],36)[0:-18] + '\n') 



def write_abs_pose_est_t1(GT_RMat_double, GT_TMat_double, frame_cnt):

    RMat_double = numpy.zeros((3, 3), dtype=numpy.float) 
    RMat_double_re = numpy.zeros((3, 3), dtype=numpy.float) 
    cv2.transpose(GT_RMat_double[frame_cnt], RMat_double)

    RVec_double = numpy.zeros((3), dtype=numpy.float) 
    #cv2.Rodrigues(RVec_double, RMat_double[frame_cnt])
    cv2.Rodrigues(RMat_double, RVec_double)

    TVec_double = numpy.zeros((3), dtype=numpy.float) 
    #print GT_RMat_double[frame_cnt]
    #print GT_TMat_double[frame_cnt]
    TVec_double = -1.0 * inv(GT_RMat_double[frame_cnt]).dot(GT_TMat_double[frame_cnt])

    #print RMat_double
    #print RVec_double
    #print TVec_double

    RMat_int= numpy.zeros((3, 3), dtype=numpy.int) 
    RVec_int= numpy.zeros((3), dtype=numpy.int) 
    TVec_int= numpy.zeros((3), dtype=numpy.int) 

    RMat_int = (RMat_double * 1024.0 * 1024.0 * 512.0).astype(int)
    RVec_int = (RVec_double * 1024.0 * 1024.0 * 1024.0 * 2.0).astype(int)
    TVec_int = (TVec_double * 1024.0 * 1024.0).astype(int)

    #print RMat_int
    #print RVec_int
    #print TVec_int
    #cv2.Rodrigues(RVec_double/2, RMat_double_re)
    #print RMat_double_re

    #RMat
    for row in range(0,3):
        for col in range(0,3):
            #print bindigits(RMat_int[row, col],32)
            USB_inst_file.write('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '0' + '0' + '00' + bindigits(RMat_int[row, col],32)[-16:] + '\n') 
            #print('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '0' + '0' + '00' + bindigits(RMat_int[row, col],32)[-16:]) 
            if(row == 2 and col == 2):
                USB_inst_file.write('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '1' + '1' + '00' + bindigits(RMat_int[row, col],32)[0:-16] + '\n') 
                #print('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '1' + '1' + '00' + bindigits(RMat_int[row, col],32)[0:-16]) 
            else:
                USB_inst_file.write('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '1' + '0' + '00' + bindigits(RMat_int[row, col],32)[0:-16] + '\n') 
                #print('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '1' + '0' + '00' + bindigits(RMat_int[row, col],32)[0:-16]) 
    #RVec
    for row in range(0,3):
        USB_inst_file.write('11' + '011000' + bindigits(row,2) + bindigits(0,2) + '0' + '0' + '00' + bindigits(RVec_int[row],32)[-16:] + '\n') 
        if(row == 2):
            USB_inst_file.write('11' + '011000' + bindigits(row,2) + bindigits(0,2) + '1' + '1' + '00' + bindigits(RVec_int[row],32)[0:-16] + '\n') 
        else:
            USB_inst_file.write('11' + '011000' + bindigits(row,2) + bindigits(0,2) + '1' + '0' + '00' + bindigits(RVec_int[row],32)[0:-16] + '\n') 

    #Tvec
    for row in range(0,3):
        USB_inst_file.write('11' + '011001' + bindigits(row,2) + bindigits(0,2) + '0' + '0' + bindigits(TVec_int[row],36)[-18:] + '\n') 
        if(row == 2):
            USB_inst_file.write('11' + '011001' + bindigits(row,2) + bindigits(0,2) + '1' + '1' + bindigits(TVec_int[row],36)[0:-18] + '\n') 
        else:
            USB_inst_file.write('11' + '011001' + bindigits(row,2) + bindigits(0,2) + '1' + '0' + bindigits(TVec_int[row],36)[0:-18] + '\n') 

    #TMat
    for row in range(0,3):
        USB_inst_file.write('11' + '010111' + bindigits(row,2) + bindigits(0,2) + '0' + '0' + bindigits(TVec_int[row],36)[-18:] + '\n') 
        if(row == 2):
            USB_inst_file.write('11' + '010111' + bindigits(row,2) + bindigits(0,2) + '1' + '1' + bindigits(TVec_int[row],36)[0:-18] + '\n') 
        else:
            USB_inst_file.write('11' + '010111' + bindigits(row,2) + bindigits(0,2) + '1' + '0' + bindigits(TVec_int[row],36)[0:-18] + '\n') 

def write_relative_pose_est_t1(GT_RMat_double, GT_TMat_double, frame_cnt):

    R1Mat_double = numpy.zeros((3, 3), dtype=numpy.float) 
    #R1Mat_double = GT_RMat_double[frame_cnt]
    cv2.transpose(GT_RMat_double[frame_cnt], R1Mat_double)
    R1Vec_double = numpy.zeros((3), dtype=numpy.float) 
    cv2.Rodrigues(R1Mat_double, R1Vec_double)

    R0Mat_double = numpy.zeros((3, 3), dtype=numpy.float) 
    #R0Mat_double = GT_RMat_double[frame_cnt-1]
    cv2.transpose(GT_RMat_double[frame_cnt-1], R0Mat_double)
    R0Vec_double = numpy.zeros((3), dtype=numpy.float) 
    cv2.Rodrigues(R0Mat_double, R0Vec_double)

    print GT_TMat_double[frame_cnt]
    print GT_TMat_double[frame_cnt-1]
    print R1Mat_double
    print R0Mat_double

    T1Vec_double = numpy.zeros((3), dtype=numpy.float) 
    T1Vec_double = -1.0 * R1Mat_double.dot(GT_TMat_double[frame_cnt])

    T0Vec_double = numpy.zeros((3), dtype=numpy.float) 
    T0Vec_double = -1.0 * R0Mat_double.dot(GT_TMat_double[frame_cnt-1])

    print T0Vec_double
    print T1Vec_double

    #####compute R_relative
    R01Mat_double = numpy.zeros((3, 3), dtype=numpy.float) 
    R01Mat_double = R1Mat_double.dot(inv(R0Mat_double))
    #R01Mat_double = inv(R0Mat_double).dot(R1Mat_double)

    #####compute T_relative
    T01Vec_double = T1Vec_double - R01Mat_double.dot(T0Vec_double)
    #T01Vec_double = inv(R0Mat_double).dot(T1Vec_double - T0Vec_double)
    #T01Vec_double = inv(R0Mat_double).dot(GT_TMat_double[frame_cnt]- GT_TMat_double[frame_cnt-1])
    #T01Vec_double = dot(GT_TMat_double[frame_cnt]- GT_TMat_double[frame_cnt-1])
    #T01Vec_double = inv(R1Mat_double).dot(GT_TMat_double[frame_cnt]) - inv(R0Mat_double).dot(GT_TMat_double[frame_cnt-1])

    R01Vec_double = numpy.zeros((3), dtype=numpy.float) 
    cv2.Rodrigues(R01Mat_double, R01Vec_double)

    print R0Vec_double
    print R1Vec_double

    print T0Vec_double
    print T1Vec_double

    print R01Mat_double
    print R01Vec_double
    print T01Vec_double

    #T1Vec_double_re = R0Mat_double.dot(T01Vec_double) + T01Vec_double 
    #print T1Vec_double_re 

    #print (R1Vec_double - R0Vec_double)
    #cv2.Rodrigues((R1Vec_double - R0Vec_double), R01Vec_double)

    RMat_int= numpy.zeros((3, 3), dtype=numpy.int) 
    RVec_int= numpy.zeros((3), dtype=numpy.int) 
    TVec_int= numpy.zeros((3), dtype=numpy.int) 

    RMat_int = (R01Mat_double * 1024.0 * 1024.0 * 512.0).astype(int)
    RVec_int = (R01Vec_double * 1024.0 * 1024.0 * 1024.0 * 2.0).astype(int)
    TVec_int = (T01Vec_double * 1024.0 * 1024.0).astype(int)

    #print RMat_int
    #print RVec_int
    #print TVec_int

    #RMat
    for row in range(0,3):
        for col in range(0,3):
            #print bindigits(RMat_int[row, col],32)
            USB_inst_file.write('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '0' + '0' + '00' + bindigits(RMat_int[row, col],32)[-16:] + '\n') 
            #print('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '0' + '0' + '00' + bindigits(RMat_int[row, col],32)[-16:]) 
            if(row == 2 and col == 2):
                USB_inst_file.write('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '1' + '1' + '00' + bindigits(RMat_int[row, col],32)[0:-16] + '\n') 
                #print('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '1' + '1' + '00' + bindigits(RMat_int[row, col],32)[0:-16]) 
            else:
                USB_inst_file.write('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '1' + '0' + '00' + bindigits(RMat_int[row, col],32)[0:-16] + '\n') 
                #print('11' + '010110' + bindigits(row,2) + bindigits(col,2) + '1' + '0' + '00' + bindigits(RMat_int[row, col],32)[0:-16]) 
    #RVec
    for row in range(0,3):
        USB_inst_file.write('11' + '011000' + bindigits(row,2) + bindigits(0,2) + '0' + '0' + '00' + bindigits(RVec_int[row],32)[-16:] + '\n') 
        if(row == 2):
            USB_inst_file.write('11' + '011000' + bindigits(row,2) + bindigits(0,2) + '1' + '1' + '00' + bindigits(RVec_int[row],32)[0:-16] + '\n') 
        else:
            USB_inst_file.write('11' + '011000' + bindigits(row,2) + bindigits(0,2) + '1' + '0' + '00' + bindigits(RVec_int[row],32)[0:-16] + '\n') 

    #Tvec
    for row in range(0,3):
        USB_inst_file.write('11' + '011001' + bindigits(row,2) + bindigits(0,2) + '0' + '0' + bindigits(TVec_int[row],36)[-18:] + '\n') 
        if(row == 2):
            USB_inst_file.write('11' + '011001' + bindigits(row,2) + bindigits(0,2) + '1' + '1' + bindigits(TVec_int[row],36)[0:-18] + '\n') 
        else:
            USB_inst_file.write('11' + '011001' + bindigits(row,2) + bindigits(0,2) + '1' + '0' + bindigits(TVec_int[row],36)[0:-18] + '\n') 

    #TMat
    for row in range(0,3):
        USB_inst_file.write('11' + '010111' + bindigits(row,2) + bindigits(0,2) + '0' + '0' + bindigits(TVec_int[row],36)[-18:] + '\n') 
        if(row == 2):
            USB_inst_file.write('11' + '010111' + bindigits(row,2) + bindigits(0,2) + '1' + '1' + bindigits(TVec_int[row],36)[0:-18] + '\n') 
        else:
            USB_inst_file.write('11' + '010111' + bindigits(row,2) + bindigits(0,2) + '1' + '0' + bindigits(TVec_int[row],36)[0:-18] + '\n') 

image_mem_banks = 2
depth_mem_banks = 2
block_size = 128
USB_inst_list=[]
USB_inst_file = open('USB_process_inst_continuous_KITTI_06_relative' + '.txt','w+')
block_row_cnt = 0
block_col_cnt = 0

#constants
USB_inst_file.write('11' + '000010' + '000000000000000101110010' + '\n') #image height
USB_inst_file.write('11' + '000011' + '000000000000010011001010' + '\n') #image_width
USB_inst_file.write('11' + '000100' + '00000000000000000011' + '0010' + '\n') #p_div + core div golden
#USB_inst_file.write('11' + '000100' + '00000000000000000101' + '0001' + '\n') #p_div + core div golden 1 10 11 100
USB_inst_file.write('11' + '000101' + '000000000000000010100000' + '\n') #core RO golden
#USB_inst_file.write('11' + '000101' + '000000000000000010000101' + '\n') #core RO
USB_inst_file.write('11' + '000110' + '000000000000000000000001' + '\n') #internal clk sel
#for dummy in range(0, 40):
for dummy in range(0, 20000000):
    USB_inst_file.write('00' + '000000' + '000000000000000000000001' + '\n') 
USB_inst_file.write('11' + '000111' + '001100000000' + '000000000000' + '\n') #inst addr
USB_inst_file.write('11' + '001000' + '001100101000' + '001100000000' + '\n') #inst addr end
#KITTI06
USB_inst_file.write('11' + '001001' + '00' + '0010110000110001011101' + '\n') #KMAT
USB_inst_file.write('11' + '001001' + '01' + '0010010110011110001101' + '\n') #KMAT
USB_inst_file.write('11' + '001001' + '10' + '0010110000110001011101' + '\n') #KMAT
USB_inst_file.write('11' + '001001' + '11' + '0000101101110001110001' + '\n') #KMAT
USB_inst_file.write('11' + '001010' + '00' + '1101101001100001110011' + '\n') #QMAT
USB_inst_file.write('11' + '001010' + '01' + '1111010010001110001111' + '\n') #QMAT
USB_inst_file.write('11' + '001010' + '10' + '0010110000110001011101' + '\n') #QMAT
USB_inst_file.write('11' + '001010' + '11' + '0000000000011101110010' + '\n') #QMAT
#KITTI03
#USB_inst_file.write('11' + '001001' + '00' + '0010110100011000100111' + '\n') #KMAT
#USB_inst_file.write('11' + '001001' + '01' + '0010011000011000111101' + '\n') #KMAT
#USB_inst_file.write('11' + '001001' + '10' + '0010110100011000100111' + '\n') #KMAT
#USB_inst_file.write('11' + '001001' + '11' + '0000101011001101101011' + '\n') #KMAT
#USB_inst_file.write('11' + '001010' + '00' + '1101100111100111000011' + '\n') #QMAT
#USB_inst_file.write('11' + '001010' + '01' + '1111010100110010010101' + '\n') #QMAT
#USB_inst_file.write('11' + '001010' + '10' + '0010110100011000100111' + '\n') #QMAT
#USB_inst_file.write('11' + '001010' + '11' + '0000000000011101110010' + '\n') #QMAT
#low
USB_inst_file.write('11' + '001011' + '000000000000000000001100' + '\n') #KEYPOINT_THRESHOLD
#mid
#USB_inst_file.write('11' + '001011' + '000000000000000000100000' + '\n') #KEYPOINT_THRESHOLD
#high
#USB_inst_file.write('11' + '001011' + '000000000000000001000000' + '\n') #KEYPOINT_THRESHOLD
#low
#USB_inst_file.write('11' + '001100' + '000000000010000000000000' + '\n') #L2_THRESHOLD
#mid
USB_inst_file.write('11' + '001100' + '000000000001000000000000' + '\n') #L2_THRESHOLD
#high
#USB_inst_file.write('11' + '001100' + '000000000000100000000000' + '\n') #L2_THRESHOLD


#initialize
initialize(USB_inst_file)

GT_RMat_double, GT_TMat_double = read_GT_pose('KITTI_VO_gray/dataset/poses/06.txt')

image_start = 1 

odd_0_even_1 = 0

for loop_cnt in range(0, 280):

    image_cnt = loop_cnt + image_start

    if(image_cnt < 10):
        img_string = 'KITTI_VO_gray/dataset/sequences/06/image_0/00000' + str(image_cnt) + '.png'
    elif(image_cnt >= 10 and image_cnt < 100):
        img_string = 'KITTI_VO_gray/dataset/sequences/06/image_0/0000' + str(image_cnt) + '.png'
    else:
        img_string = 'KITTI_VO_gray/dataset/sequences/06/image_0/000' + str(image_cnt) + '.png'

    if(image_cnt < 10):
        depth_string = 'KITTI_VO_gray/dataset/sequences/06/depth/00000' + str(image_cnt) + '.png'
    elif(image_cnt >= 10 and image_cnt < 100):
        depth_string = 'KITTI_VO_gray/dataset/sequences/06/depth/0000' + str(image_cnt) + '.png'
    else:
        depth_string = 'KITTI_VO_gray/dataset/sequences/06/depth/000' + str(image_cnt) + '.png'

    img=scipy.misc.imread(img_string)
    [image_height, image_width] = img.shape
    print str(image_height) + 'x' + str(image_width)
    img.astype(int)
    image_block = numpy.zeros((block_size, block_size), dtype=numpy.int) 
    depth_img=scipy.misc.imread(depth_string)
    [depth_height, depth_width] = depth_img.shape
    print str(depth_height) + 'x' + str(depth_width)
    depth_img.astype(int)
    depth_block = numpy.zeros((block_size, block_size), dtype=numpy.int) 

    #KITTI
    write_abs_pose_est_t0(GT_RMat_double, GT_TMat_double, 0) ###always initialize pose to be 0
    write_abs_pose_est_t1(GT_RMat_double, GT_TMat_double, 0) 

    print "start frame 0: " + str(image_cnt)

    row_blocks = int(image_height / 96) + 1
    col_blocks = int((image_width - 64) / 96) + 1

    USB_inst_file.write('11' + '001111' + '000000000000000000000001' + '\n') #first frame

    USB_inst_file.write('11' + '001110' + '000000000000000' + '000' + '001' + '010' + '\n') #switch buffer

    for block_row_cnt in range(0, row_blocks):
        for block_col_cnt in range(1, col_blocks):

            #first block
            if(block_row_cnt == 0 and block_col_cnt == 1): 
            #if(block_row_cnt == 1 and block_col_cnt == 5): 
                #write first image and depth block
                image_block = copy.deepcopy(img[block_row_cnt*96:block_row_cnt*96+128, 64+block_col_cnt*96:64+block_col_cnt*96+128])
                image_block -= 128
                depth_block = depth_img[block_row_cnt*96:block_row_cnt*96+128, 64+block_col_cnt*96:64+block_col_cnt*96+128]
                write_image_block(image_block, block_size, USB_inst_file, odd_0_even_1)
                write_depth_block(depth_block, block_size, USB_inst_file, odd_0_even_1)
                USB_inst_file.write('11' + '001101' + str(bindigits(block_row_cnt*96, 12)) + str(bindigits(64+block_col_cnt*96, 12)) + '\n') #BLOCK OFFSET
            else:
                USB_inst_file.write('11' + '010010' + '000000000000000010000000' + '\n') #SWITCH BUFFER
                #extract keypoint on current block
                USB_inst_file.write('11' + '010010' + '000000000000000000000001' + '\n') #LOAD INSTRUCTION ADDR, process keypoint
                USB_inst_file.write('11' + '010010' + '000000000000000000100000' + '\n') #START CNN keypoint && pose estimation

                if(odd_0_even_1 == 0):
                    odd_0_even_1 = 1
                else:
                    odd_0_even_1 = 0

                #write next image and depth block at the same time
                image_block = copy_img_block(img, block_row_cnt, block_col_cnt, image_height, image_width)
                depth_block = copy_depth_block(depth_img, block_row_cnt, block_col_cnt, image_height, image_width)

                write_image_block(image_block, block_size, USB_inst_file, odd_0_even_1)
                write_depth_block(depth_block, block_size, USB_inst_file, odd_0_even_1)

                USB_inst_file.write('11' + '010011' + '000000000000000000000001' + '\n') #stop read
                add_junk(USB_inst_file)
                #chip is waked up when keypoints finishes
                USB_inst_file.write('11' + '010010' + '000000000000000000000010' + '\n') #LOAD INSTRUCTION ADDR, process feature 
                USB_inst_file.write('11' + '010010' + '000000000000000001100000' + '\n') #START CNN
                USB_inst_file.write('11' + '010011' + '000000000000000000000001' + '\n') #stop read

                #junk
                add_junk(USB_inst_file)
                #update block offset
                USB_inst_file.write('11' + '001101' + str(bindigits(block_row_cnt*96, 12)) + str(bindigits(64+block_col_cnt*96, 12)) + '\n') #BLOCK OFFSET

    #process last block
    USB_inst_file.write('11' + '010010' + '000000000000000010000000' + '\n') #SWITCH BUFFER

    #extract keypoint on current block
    USB_inst_file.write('11' + '010010' + '000000000000000000000001' + '\n') #LOAD INSTRUCTION ADDR, process keypoint
    USB_inst_file.write('11' + '010010' + '000000000000000000100000' + '\n') #START CNN keypoint && pose estimation
    USB_inst_file.write('11' + '010011' + '000000000000000000000001' + '\n') #stop read
    add_junk(USB_inst_file)

    if(odd_0_even_1 == 0):
        odd_0_even_1 = 1
    else:
        odd_0_even_1 = 0

    #chip is waked up when keypoints finishes
    USB_inst_file.write('11' + '010010' + '000000000000000000000010' + '\n') #LOAD INSTRUCTION ADDR, process feature 
    USB_inst_file.write('11' + '010010' + '000000000000000001100000' + '\n') #START CNN
    USB_inst_file.write('11' + '010011' + '000000000000000000000001' + '\n') #stop read
    add_junk(USB_inst_file)

    #PnP
    USB_inst_file.write('11' + '010010' + '000000000000000000001000' + '\n') #START PnP 
    USB_inst_file.write('11' + '010011' + '000000000000000000000001' + '\n') #stop read
    USB_inst_file.write('11' + '001111' + '000000000000000000000000' + '\n') #first frame
    add_junk(USB_inst_file)

    # start frame 1 
    print "start frame 1"

    image_cnt = loop_cnt + image_start + 1

    if(image_cnt < 10):
        img_string = 'KITTI_VO_gray/dataset/sequences/06/image_0/00000' + str(image_cnt) + '.png'
    elif(image_cnt >= 10 and image_cnt < 100):
        img_string = 'KITTI_VO_gray/dataset/sequences/06/image_0/0000' + str(image_cnt) + '.png'
    else:
        img_string = 'KITTI_VO_gray/dataset/sequences/06/image_0/000' + str(image_cnt) + '.png'

    if(image_cnt < 10):
        depth_string = 'KITTI_VO_gray/dataset/sequences/06/depth/00000' + str(image_cnt) + '.png'
    elif(image_cnt >= 10 and image_cnt < 100):
        depth_string = 'KITTI_VO_gray/dataset/sequences/06/depth/0000' + str(image_cnt) + '.png'
    else:
        depth_string = 'KITTI_VO_gray/dataset/sequences/06/depth/000' + str(image_cnt) + '.png'

    img=scipy.misc.imread(img_string)
    [image_height, image_width] = img.shape
    print str(image_height) + 'x' + str(image_width)
    img.astype(int)
    image_block = numpy.zeros((block_size, block_size), dtype=numpy.int) 
    depth_img=scipy.misc.imread(depth_string)
    [depth_height, depth_width] = depth_img.shape
    print str(depth_height) + 'x' + str(depth_width)
    depth_img.astype(int)
    depth_block = numpy.zeros((block_size, block_size), dtype=numpy.int) 

    row_blocks = int(image_height / 96) + 1
    col_blocks = int((image_width - 64) / 96) + 1

    #odd_0_even_1 = 0
    # RMat t0, t1, t2, TMat t0, t1, t2 
    #USB_inst_file.write('11' + '010010' + '000000000000000100000000' + '\n') #R,T proceed
    # curr, prev index

    USB_inst_file.write('11' + '001110' + '000000000000000' + '001' + '000' + '010' + '\n') #switch buffer

    #pose estimation
    write_relative_pose_est_t1(GT_RMat_double, GT_TMat_double, image_cnt-1) 

    for block_row_cnt in range(0, row_blocks):
        for block_col_cnt in range(1, col_blocks):

            #first block
            if(block_row_cnt == 0 and block_col_cnt == 1): 
                #write first image and depth block
                image_block = copy.deepcopy(img[block_row_cnt*96:block_row_cnt*96+128, 64+block_col_cnt*96:64+block_col_cnt*96+128])
                image_block -= 128
                depth_block = depth_img[block_row_cnt*96:block_row_cnt*96+128, 64+block_col_cnt*96:64+block_col_cnt*96+128]
                write_image_block(image_block, block_size, USB_inst_file, odd_0_even_1)
                write_depth_block(depth_block, block_size, USB_inst_file, odd_0_even_1)
                USB_inst_file.write('11' + '001101' + str(bindigits(block_row_cnt*96, 12)) + str(bindigits(64+block_col_cnt*96, 12)) + '\n') #BLOCK OFFSET
            else:
                USB_inst_file.write('11' + '010010' + '000000000000000010000000' + '\n') #SWITCH BUFFER
                #extract keypoint on current block
                USB_inst_file.write('11' + '010010' + '000000000000000000000001' + '\n') #LOAD INSTRUCTION ADDR, process keypoint
                USB_inst_file.write('11' + '010010' + '000000000000000000100000' + '\n') #START CNN keypoint && pose estimation

                if(odd_0_even_1 == 0):
                    odd_0_even_1 = 1
                else:
                    odd_0_even_1 = 0

                #write next image and depth block at the same time
                image_block = copy_img_block(img, block_row_cnt, block_col_cnt, image_height, image_width)
                depth_block = copy_depth_block(depth_img, block_row_cnt, block_col_cnt, image_height, image_width)
                #print image_block

                write_image_block(image_block, block_size, USB_inst_file, odd_0_even_1)
                write_depth_block(depth_block, block_size, USB_inst_file, odd_0_even_1)

                USB_inst_file.write('11' + '010011' + '000000000000000000000001' + '\n') #stop read
                add_junk(USB_inst_file)
                #chip is waked up when keypoints finishes
                USB_inst_file.write('11' + '010010' + '000000000000000000000010' + '\n') #LOAD INSTRUCTION ADDR, process feature 
                USB_inst_file.write('11' + '010010' + '000000000000000001100000' + '\n') #START CNN

                USB_inst_file.write('11' + '010011' + '000000000000000000000001' + '\n') #stop read

                #junk
                add_junk(USB_inst_file)
                #update block offset
                USB_inst_file.write('11' + '001101' + str(bindigits(block_row_cnt*96, 12)) + str(bindigits(64+block_col_cnt*96, 12)) + '\n') #BLOCK OFFSET

    #process last block
    USB_inst_file.write('11' + '010010' + '000000000000000010000000' + '\n') #SWITCH BUFFER
    #extract keypoint on current block
    USB_inst_file.write('11' + '010010' + '000000000000000000000001' + '\n') #LOAD INSTRUCTION ADDR, process keypoint
    USB_inst_file.write('11' + '010010' + '000000000000000000100000' + '\n') #START CNN keypoint && pose estimation
    USB_inst_file.write('11' + '010011' + '000000000000000000000001' + '\n') #stop read
    add_junk(USB_inst_file)

    if(odd_0_even_1 == 0):
        odd_0_even_1 = 1
    else:
        odd_0_even_1 = 0

    #chip is waked up when keypoints finishes
    USB_inst_file.write('11' + '010010' + '000000000000000000000010' + '\n') #LOAD INSTRUCTION ADDR, process feature 
    USB_inst_file.write('11' + '010010' + '000000000000000001100000' + '\n') #START CNN
    USB_inst_file.write('11' + '010011' + '000000000000000000000001' + '\n') #stop read
    add_junk(USB_inst_file)

    #PnP
    #write_relative_pose_est_t1(GT_RMat_double, GT_TMat_double, image_cnt) 
    add_junk(USB_inst_file)
    USB_inst_file.write('11' + '010010' + '000000000000000000001000' + '\n') #START PnP 
    USB_inst_file.write('11' + '010011' + '000000000000000000000001' + '\n') #stop read
    add_junk(USB_inst_file)

    #read pose out
    print(bindigits(loop_cnt * 2 + 1, 9))
    USB_inst_file.write('11' + '000001' + '11101' + '0000000000' + bindigits(loop_cnt * 2 + 1, 9) + '\n') #read to register
    for dummy in range(0, 1):
        add_junk(USB_inst_file)
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '00' + '011010' + '\n') #R0 lower
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '00' + '011010' + '\n') #R0 upper 
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '01' + '011010' + '\n') #R1 lower
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '01' + '011010' + '\n') #R1 upper 
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '10' + '011010' + '\n') #R2 lower
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '10' + '011010' + '\n') #R2 upper 
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '00' + '011011' + '\n') #T0 lower
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '00' + '011011' + '\n') #T0 upper 
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '01' + '011011' + '\n') #T1 lower
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '01' + '011011' + '\n') #T1 upper 
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '10' + '011011' + '\n') #T2 lower
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '10' + '011011' + '\n') #T2 upper 
        USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '10' + '000100' + '\n') #P_DIV
    add_junk(USB_inst_file)

for dummy in range(0, 1024):
    add_junk(USB_inst_file)
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '00' + '011010' + '\n') #R0 lower
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '00' + '011010' + '\n') #R0 upper 
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '01' + '011010' + '\n') #R1 lower
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '01' + '011010' + '\n') #R1 upper 
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '10' + '011010' + '\n') #R2 lower
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '10' + '011010' + '\n') #R2 upper 
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '00' + '011011' + '\n') #T0 lower
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '00' + '011011' + '\n') #T0 upper 
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '01' + '011011' + '\n') #T1 lower
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '01' + '011011' + '\n') #T1 upper 
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '0' + '10' + '011011' + '\n') #T2 lower
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '10' + '011011' + '\n') #T2 upper 
    USB_inst_file.write('11' + '000001' + '1000' + '00000000000' + '1' + '10' + '000100' + '\n') #P_DIV
add_junk(USB_inst_file)



