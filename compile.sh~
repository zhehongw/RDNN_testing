#!bin/bash
####### choose which test to run
if [ -z "$1" ]; then
  echo "Please provide which dataset to run or which output to construct"
  echo "KITTI midderbury etc... "
  echo "image video etc... "
  exit
fi
test=$1


if [ $test == "KITTI" ] || [ $test == "ZED_LR_HD_2" ] || [ $test == "ZED_LR_720" ] || [ $test == "ZED_LR_720_2" ] || [ $test == "ZED_LR_VGA" ] || [ $test == "ZED_LR_HD" ] || [ $test == "KITTI_LR" ] || [ $test == "KITTI_LR1" ] || [ $test == "flyer_test" ] || [ $test == "flyer_test_LR" ] ||[ $test == "flyer_test_LR0" ] || [ $test == "flyer_test_LR1" ] || [ $test == "flyer_test_LR2" ] || [ $test == "flyer_test_LR3" ] || [ $test == "flyer_test_LR4" ] || [ $test == "flyer_test1" ] || [ $test == "flyer_test2" ] || [ $test == "flyer_test3" ] ||  [ $test == "flyer_test4" ] || [ $test == "ZED_LR_VGA" ] || [ $test == "50_generate_2_image" ] || [ $test == "50_generate_2_image_no_buffer" ] || [ $test == "50_generate_2_image_usb" ]; then 
	g++ -ggdb `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o  `basename scanned_ESGN_$1.c .c` global.c stream_usb.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0`
elif [ $test == "50_generate_2_image_usb_once" ]; then
	g++ -ggdb `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_once.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0`
elif [ $test == "50_generate_2_image_usb_vector" ]; then
	g++ -ggdb -lm -lpthread -lz `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0` -lm -lpthread -lz 
elif [ $test == "50_generate_2_image_usb_vector_image" ]; then
	g++ -ggdb -lm -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0` -lm -lpthread -lz
elif [ $test == "50_generate_2_image_usb_vector_HD" ]; then
	g++ -ggdb -lm -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0` -lm -lpthread -lz
elif [ $test == "50_generate_2_image_usb_vector_HD_LR" ]; then
	g++ -ggdb -lm -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0` -lm -lpthread -lz
elif [ $test == "50_generate_2_image_usb_vector_HD_LR_1024_buffer" ]; then
	g++ -ggdb -lm -pg -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector_1024_buffer.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0` -lm -lpthread -lz
elif [ $test == "50_generate_2_image_usb_vector_HD_LR_1024_buffer_long" ]; then
	g++ -ggdb -lm -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector_1024_buffer.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0` -lm -lpthread -lz
elif [ $test == "50_generate_2_image_usb_vector_ZE_VGA_LR_1024_buffer" ]; then
    g++ -O3 -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector_1024_buffer.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0 ` -lpthread
elif [ $test == "50_generate_2_image_usb_vector_ZE_VGA_LR_1024_buffer_parallel" ]; then
    g++ -O3 -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector_1024_buffer.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0 ` -lpthread
elif [ $test == "50_generate_2_image_usb_vector_ZE_VGA_LR_1024_buffer_parallel_cap" ]; then
    g++ -O3 -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector_1024_buffer.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0 ` -lpthread
elif [ $test == "50_generate_2_image_usb_vector_1024_buffer" ]; then
	g++ -ggdb `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector_1024_buffer.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0`
elif [ $test == "JPL_flyer_test" ]; then
    g++ -O3 -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector_1024_buffer.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0 ` -lpthread
elif [ $test == "JPL_flyer_test_zed" ]; then
    g++ -O3 -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector_1024_buffer.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0 ` -lpthread
elif [ $test == "JPL_flyer_test_zed_HD" ]; then
    g++ -O3 -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename scanned_ESGN_$1.c .c` stream_usb_vector_1024_buffer.c scanned_ESGN_$1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0 ` -lpthread
elif [ $test == "stream_in_to_file" ]; then
	g++ -ggdb `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename $1.c .c` $1.c `pkg-config --libs libusb-1.0`
elif [ $test == "stream_in_demo" ]; then
	g++ -ggdb -lm -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename $1.c .c` colormap.cpp $1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0`
elif [ $test == "stream_in_demo_parallel" ]; then
	g++ -ggdb -lm -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename $1.c .c` colormap.cpp $1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0` -lpthread
elif [ $test == "stream_in_demo_parallel_changed" ]; then
	g++ -ggdb -lm -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename $1.c .c` colormap.cpp $1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0` -lpthread
elif [ $test == "stream_in_demo_parallel_changed_HD" ]; then
	g++ -ggdb -lm -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename $1.c .c` colormap.cpp $1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0` -lpthread
elif [ $test == "rectify_image" ]; then
	g++ -ggdb `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename $1.c .c` stream_usb_vector.c $1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0`
else
	g++ -ggdb `pkg-config --cflags opencv` -o `basename construct_$1_from_vector.c .c` colormap.cpp construct_$1_from_vector.c `pkg-config --libs opencv`
	#g++ -ggdb `pkg-config --cflags opencv` -o `basename video_gerator.cpp .cpp` colormap.cpp video_gerator.cpp `pkg-config --libs opencv`
fi
