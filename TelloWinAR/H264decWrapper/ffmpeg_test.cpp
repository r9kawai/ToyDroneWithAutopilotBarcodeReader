#include "std.h"

extern "C" {
#include <libavutil/imgutils.h>
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libswscale/swscale.h>
}
#include <opencv2/opencv.hpp>
#include <opencv2/core.hpp>
#include <opencv2/core/utility.hpp>
#include <opencv2/highgui.hpp>

int fcounter = 0;

void on_frame_decoded(AVFrame* frame) {
//	printf("Frame decoded PTS: %jd\n", frame->pts);
	fcounter++;
	printf("Frame decoded %09d %dx%d PTS: %jd\n", fcounter, frame->width, frame->height, frame->pts);
}

void ColorConvert(AVFrame* frame, AVFrame* rgb_frame, unsigned char* out_rgb)
{
	int w = frame->width;
	int h = frame->height;
	int pix_fmt = frame->format;

	SwsContext* sws_context = NULL;
	sws_context = sws_getCachedContext(sws_context, w, h, (AVPixelFormat)pix_fmt, w, h, AV_PIX_FMT_BGR24, SWS_BILINEAR, NULL, NULL, NULL);
	if (!sws_context) {
		throw "H264decWrapper::cannot allocate context";
	}

	avpicture_fill((AVPicture*)rgb_frame, out_rgb, AV_PIX_FMT_RGB24, w, h);
	sws_scale(sws_context, frame->data, frame->linesize, 0, h, rgb_frame->data, rgb_frame->linesize);
	rgb_frame->width = w;
	rgb_frame->height = h;
	return;
}

int main(int argc, char* argv[])
{
	std::cout << "ffmpeg_test.cpp main()" << std::endl;
	std::cout << "Boost version:" << BOOST_LIB_VERSION << std::endl;
	std::cout << "OpenCV version:" << CV_VERSION << std::endl;
	std::cout << "FFmpeg" << avutil_configuration() << avutil_license << std::endl;

	av_register_all();
	boost::system::error_code err;

	char* input_path = NULL;
//	const char* input_path = "..\\H264decWrapper\\video_rcv.bin";
	if (argc == 2) {
		if (argv[1]) {
			input_path = argv[1];
			bool exist = boost::filesystem::exists(input_path, err);
			if (!exist || err) {
				std::cout << "no file." << std::endl;
				return -1;
			}
			else {
				std::cout << input_path << " decode start." << std::endl;
			}
		}
	}
	else {
		return -1;
	}
	AVFormatContext* format_context = nullptr;
	if (avformat_open_input(&format_context, input_path, nullptr, nullptr) != 0) {
		printf("avformat_open_input failed\n");
	}

	if (avformat_find_stream_info(format_context, nullptr) < 0) {
		printf("avformat_find_stream_info failed\n");
	}

	AVStream* video_stream = nullptr;
	for (int i = 0; i < (int)format_context->nb_streams; ++i) {
		if (format_context->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
			video_stream = format_context->streams[i];
			break;
		}
	}
	if (video_stream == nullptr) {
		printf("No video stream ...\n");
	}

	AVCodec* codec = avcodec_find_decoder(video_stream->codecpar->codec_id);
	if (codec == nullptr) {
		printf("No supported decoder ...\n");
	}

	AVCodecContext* codec_context = avcodec_alloc_context3(codec);
	if (codec_context == nullptr) {
		printf("avcodec_alloc_context3 failed\n");
	}

	if (avcodec_parameters_to_context(codec_context, video_stream->codecpar) < 0) {
		printf("avcodec_parameters_to_context failed\n");
	}
	
	if (avcodec_open2(codec_context, codec, nullptr) != 0) {
		printf("avcodec_open2 failed\n");
	}

	AVFrame* frame = av_frame_alloc();
	AVFrame* rgb_frame = av_frame_alloc();
	AVPacket packet = AVPacket();

	cv::Mat decode_img;
	const int VIDEO_WIDTH = 960;
	const int VIDEO_HEIGHT = 720;
	decode_img = cv::Mat::zeros(VIDEO_HEIGHT, VIDEO_WIDTH, CV_8UC3);

	cv::namedWindow("CVWINNAME_1");
	cv::imshow("CVWINNAME_1", decode_img);

	bool key_exit = false;
	while (av_read_frame(format_context, &packet) == 0 && key_exit == false) {
		if (packet.stream_index == video_stream->index) {
			if (avcodec_send_packet(codec_context, &packet) != 0) {
				printf("avcodec_send_packet failed\n");
			}
			while (avcodec_receive_frame(codec_context, frame) == 0 && key_exit == false) {
				on_frame_decoded(frame);

				ColorConvert(frame, rgb_frame, decode_img.data);
				cv::imshow("CVWINNAME_1", decode_img);
				if (cv::waitKey(5) == 27) {
					key_exit = true;
				}
			}
		}
		av_packet_unref(&packet);
	}

	// flush decoder
	if (avcodec_send_packet(codec_context, nullptr) != 0) {
		printf("avcodec_send_packet failed");
	}

	while (avcodec_receive_frame(codec_context, frame) == 0) {
		on_frame_decoded(frame);
	}

	av_frame_free(&frame);
	avcodec_free_context(&codec_context);
	avformat_close_input(&format_context);

	return 0;
}

// EOF
