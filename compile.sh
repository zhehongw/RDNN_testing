#!bin/bash
####### choose which test to run
if [ -z "$1" ]; then
  echo "Please provide which dataset to run or which output to construct"
  echo "KITTI midderbury etc... "
  echo "image video etc... "
  exit
fi
test=$1


if [ $test == "ReRAM_from_file_test" ]; then
    g++ -ggdb -O3 -fno-stack-protector -lpthread `pkg-config --cflags opencv` `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename $1.c .c` stream_usb_vector_1024_buffer.c $1.c `pkg-config --libs opencv` `pkg-config --libs libusb-1.0 ` -lpthread
elif [ $test == "stream_in_to_file" ]; then
	g++ -ggdb `pkg-config --cflags libusb-1.0` -std=c++11 -o `basename $1.c .c` $1.c `pkg-config --libs libusb-1.0`
else
	g++ -ggdb `pkg-config --cflags opencv` -o `basename construct_$1_from_vector.c .c` colormap.cpp construct_$1_from_vector.c `pkg-config --libs opencv`
	#g++ -ggdb `pkg-config --cflags opencv` -o `basename video_gerator.cpp .cpp` colormap.cpp video_gerator.cpp `pkg-config --libs opencv`
fi
