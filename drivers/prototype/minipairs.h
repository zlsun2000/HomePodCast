// HomePodCast endpoint registration. MIT license.
#pragma once
#include "speakertopo.h"
#include "speakertoptable.h"
#include "homepodcastwavtable.h"

NTSTATUS CreateMiniportWaveRTSYSVAD(PUNKNOWN*, REFCLSID, PUNKNOWN, POOL_FLAGS,
                                  PUNKNOWN, PVOID, PENDPOINT_MINIPAIR);
NTSTATUS CreateMiniportTopologySYSVAD(PUNKNOWN*, REFCLSID, PUNKNOWN, POOL_FLAGS,
                                    PUNKNOWN, PVOID, PENDPOINT_MINIPAIR);

static PHYSICALCONNECTIONTABLE HomePodCastPhysicalConnections[] =
{
    { KSPIN_TOPO_WAVEOUT_SOURCE, 1, CONNECTIONTYPE_WAVE_OUTPUT }
};
static ENDPOINT_MINIPAIR HomePodCastMiniports =
{
    eSpeakerDevice,
    L"TopologyHomePodCast", NULL, CreateMiniportTopologySYSVAD,
    &SpeakerTopoMiniportFilterDescriptor, 0, NULL,
    L"WaveHomePodCast", NULL, CreateMiniportWaveRTSYSVAD,
    &HomePodCastWaveDescriptor, 0, NULL,
    2, HomePodCastPinFormats, SIZEOF_ARRAY(HomePodCastPinFormats),
    HomePodCastPhysicalConnections, SIZEOF_ARRAY(HomePodCastPhysicalConnections),
    ENDPOINT_NO_FLAGS, NULL, 0, NULL
};
static PENDPOINT_MINIPAIR g_RenderEndpoints[] = { &HomePodCastMiniports };
#define g_cRenderEndpoints SIZEOF_ARRAY(g_RenderEndpoints)
// The upstream registration routine accepts a zero count; no capture device
// exists. WASAPI loopback is opened on the render endpoint itself.
static PENDPOINT_MINIPAIR* g_CaptureEndpoints = NULL;
static ULONG g_cCaptureEndpoints = 0;
#define g_MaxMiniports 2
