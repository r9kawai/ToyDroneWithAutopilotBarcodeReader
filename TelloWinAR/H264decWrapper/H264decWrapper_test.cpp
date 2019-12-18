/**
* @brief
* H264decWrapper test run code
*/
#include "std.h"
#include <opencv2/opencv.hpp>
#include <opencv2/core.hpp>
#include <opencv2/core/utility.hpp>
#include <opencv2/highgui.hpp>
#include "H264decWrapper.h"

int _main_disable_(int argc, char* argv[])
{
	std::cout << "H264decWrapper_test.cpp main()" << std::endl;
	std::cout << "Boost version:" << BOOST_LIB_VERSION << std::endl;
	std::cout << "OpenCV version:" << CV_VERSION << std::endl;

	const int VIDEO_WIDTH = 960;
	const int VIDEO_HEIGHT = 720;
	const int FRAME_SAVE = 5;
	const int READ_SEND_SIZE = 2048;

	cv::Mat decode_img;
	decode_img = cv::Mat::zeros(VIDEO_HEIGHT, VIDEO_WIDTH, CV_8UC3);
	const char* CVWINNAME_1 = "H264decWrapper_test";
	cv::namedWindow("CVWINNAME_1");
	cv::imshow("CVWINNAME_1", decode_img);

	FILE *fhd = std::fopen("video_rcv.bin", "rb");
	if (fhd == NULL) {
		std::cout << "no file." << std::endl;
		return -1;
	}
	try {
		AVFrame* avframe;
		H264decWrapper h264dec;
		long long int pts = 0;

		bool on_decode = true;
		while (on_decode) {
			unsigned char buff[READ_SEND_SIZE];
			int rsize = (int)std::fread(buff, 1, READ_SEND_SIZE, fhd);
			if (rsize < READ_SEND_SIZE) {
				on_decode = false;
			}

			h264dec.Parse(buff, rsize);
			if (h264dec.FrameAvailable(&pts)) {
				avframe = h264dec.DecodeFrame();
				if (avframe->width == VIDEO_WIDTH && avframe->height == VIDEO_HEIGHT) {
					h264dec.ColorConvert(avframe, decode_img.data);
				}
			}

			cv::imshow("CVWINNAME_1", decode_img);
			if (cv::waitKey(1) == 27) {
				break;
			}
		}
	}
	catch (char* errmsg) {
		std::cout << errmsg << std::endl;
	}
	std::fclose(fhd);

	cv::destroyAllWindows();
	return 0;
}

// EOF