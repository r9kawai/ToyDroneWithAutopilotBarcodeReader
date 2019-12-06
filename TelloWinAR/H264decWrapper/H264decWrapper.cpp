/**
* @brief
* H264decWrapper class to wrap a h264 video decoder in libffmpeg
*/
#include "std.h"
#include "H264decWrapper.h"

/**
* @brief
* H264decWrapper class : constracter
*/
H264decWrapper::H264decWrapper()
	: m_codec_context(NULL)
	, m_frame(NULL)
	, m_codec(NULL)
	, m_parser(NULL)
	, m_pkt(NULL)
	, m_sws_context(NULL)
	, m_framergb(NULL)
{
	std::cout << "H264decWrapper::H264decWrapper()" << std::endl;
	std::cout << "FFmpeg" << avutil_configuration() << avutil_license << std::endl;
	avcodec_register_all();

	m_codec = avcodec_find_decoder(AV_CODEC_ID_H264);
	if (!m_codec) {
		throw "H264decWrapper::cannot find decoder";
	}

	m_codec_context = avcodec_alloc_context3(m_codec);
	if (!m_codec_context) {
		throw "H264decWrapper::cannot allocate context";
	}

	if (m_codec->capabilities & AV_CODEC_CAP_TRUNCATED) {
		m_codec_context->flags |= AV_CODEC_FLAG_TRUNCATED;
	}

	int err = avcodec_open2(m_codec_context, m_codec, nullptr);
	if (err < 0) {
		throw "H264decWrapper::cannot open context";
	}

	m_parser = av_parser_init(AV_CODEC_ID_H264);
	if (!m_parser) {
		throw "H264decWrapper::cannot init parser";
	}

	m_frame = av_frame_alloc();
	if (!m_frame) {
		throw "H264decWrapper::cannot allocate frame";
	}

	m_pkt = new AVPacket;
	if (!m_pkt) {
		throw "H264decWrapper::cannot allocate packet";
	}
	av_init_packet(m_pkt);

	m_framergb = av_frame_alloc();
	if (!m_framergb) {
		throw "H264decWrapper::cannot allocate frame";
	}
	return;
}

/**
* @brief
* H264decWrapper class : destracter
*/
H264decWrapper::~H264decWrapper()
{
	av_parser_close(m_parser);
	avcodec_close(m_codec_context);
	av_free(m_codec_context);
	av_frame_free(&m_frame);
	delete m_pkt;

	sws_freeContext(m_sws_context);
	av_frame_free(&m_framergb);
	return;
}

/**
* @brief
* H264decWrapper class : parse decode data
*/
int H264decWrapper::Parse(const unsigned char* in_data, int in_size)
{
	int nread = av_parser_parse2(m_parser, m_codec_context, &m_pkt->data, &m_pkt->size, in_data, in_size, 0, 0, AV_NOPTS_VALUE);
	return nread;
}

bool H264decWrapper::FrameAvailable(long long int* pts)
{
	if (m_pkt->size > 0) {
		*pts = m_pkt->pts;
		return true;
	}
	else {
		return false;
	}
}

AVFrame* H264decWrapper::DecodeFrame()
{
	int got_picture = 0;
	int nread = avcodec_decode_video2(m_codec_context, m_frame, &got_picture, m_pkt);
//	if (nread < 0 || got_picture == 0) {
//		throw "H264decWrapper::error decoding frame";
//	}
	return m_frame;
}

AVFrame* H264decWrapper::ColorConvert(AVFrame *frame, unsigned char* out_rgb)
{
	int w = frame->width;
	int h = frame->height;
	int pix_fmt = frame->format;

	m_sws_context = sws_getCachedContext(m_sws_context, w, h, (AVPixelFormat)pix_fmt, w, h, AV_PIX_FMT_BGR24, SWS_BILINEAR, NULL, NULL, NULL);
	if (!m_sws_context) {
		throw "H264decWrapper::cannot allocate context";
	}

	avpicture_fill((AVPicture*)m_framergb, out_rgb, AV_PIX_FMT_RGB24, w, h);
	sws_scale(m_sws_context, frame->data, frame->linesize, 0, h, m_framergb->data, m_framergb->linesize);
	m_framergb->width = w;
	m_framergb->height = h;
	return m_framergb;
}

int H264decWrapper::PredictSize(int w, int h)
{
	int s;
	s = avpicture_fill((AVPicture*)m_framergb, nullptr, AV_PIX_FMT_RGB24, w, h);
	return s;
}

// EOF