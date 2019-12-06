/**
* @brief
* H264decWrapper class header
*/
#pragma once
#include "std.h"
extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/avutil.h>
#include <libavutil/mem.h>
#include <libswscale/swscale.h>
}

class H264decWrapper
{
public:
	enum H264decWrapper_err {
		DECODE_OK,
		DECODE_OPEN_ERR,
	};

public:
	H264decWrapper();
	~H264decWrapper();
	int Parse(const unsigned char* in_data, int in_size);
	bool FrameAvailable(long long int* pts);
	AVFrame* DecodeFrame();
	AVFrame* ColorConvert(AVFrame* frame, unsigned char* out_rgb);
	int PredictSize(int w, int h);

private:
	AVCodecContext* m_codec_context;
	AVFrame* m_frame;
	AVCodec* m_codec;
	AVCodecParserContext* m_parser;
	AVPacket* m_pkt;

	SwsContext* m_sws_context;
	AVFrame* m_framergb;
};

// EOF