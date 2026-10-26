// HomePodCast shared-mode virtual render endpoint. MIT license.
// The upstream miniport implementation remains under the Microsoft MS-PL license.
#pragma once

// No hardware audio-engine node, offload pin, or hardware loopback pin is
// advertised. Windows Audio Engine owns mixing and WASAPI software loopback.
static KSDATAFORMAT_WAVEFORMATEXTENSIBLE HomePodCastFormats[] =
{
    {
        { sizeof(KSDATAFORMAT_WAVEFORMATEXTENSIBLE), 0, 0, 0,
          STATICGUIDOF(KSDATAFORMAT_TYPE_AUDIO), STATICGUIDOF(KSDATAFORMAT_SUBTYPE_PCM),
          STATICGUIDOF(KSDATAFORMAT_SPECIFIER_WAVEFORMATEX) },
        { { WAVE_FORMAT_EXTENSIBLE, 2, 48000, 192000, 4, 16,
            sizeof(WAVEFORMATEXTENSIBLE) - sizeof(WAVEFORMATEX) },
          16, KSAUDIO_SPEAKER_STEREO, STATICGUIDOF(KSDATAFORMAT_SUBTYPE_PCM) }
    },
    {
        { sizeof(KSDATAFORMAT_WAVEFORMATEXTENSIBLE), 0, 0, 0,
          STATICGUIDOF(KSDATAFORMAT_TYPE_AUDIO), STATICGUIDOF(KSDATAFORMAT_SUBTYPE_PCM),
          STATICGUIDOF(KSDATAFORMAT_SPECIFIER_WAVEFORMATEX) },
        { { WAVE_FORMAT_EXTENSIBLE, 2, 44100, 176400, 4, 16,
            sizeof(WAVEFORMATEXTENSIBLE) - sizeof(WAVEFORMATEX) },
          16, KSAUDIO_SPEAKER_STEREO, STATICGUIDOF(KSDATAFORMAT_SUBTYPE_PCM) }
    }
};
static MODE_AND_DEFAULT_FORMAT HomePodCastModes[] =
{
    { STATIC_AUDIO_SIGNALPROCESSINGMODE_RAW, &HomePodCastFormats[0].DataFormat },
    { STATIC_AUDIO_SIGNALPROCESSINGMODE_DEFAULT, &HomePodCastFormats[0].DataFormat }
};
static PIN_DEVICE_FORMATS_AND_MODES HomePodCastPinFormats[] =
{
    { SystemRenderPin, HomePodCastFormats, SIZEOF_ARRAY(HomePodCastFormats),
      HomePodCastModes, SIZEOF_ARRAY(HomePodCastModes) },
    { BridgePin, NULL, 0, NULL, 0 }
};
static KSDATARANGE_AUDIO HomePodCastRange =
{
    { sizeof(KSDATARANGE_AUDIO), KSDATARANGE_ATTRIBUTES, 0, 0,
      STATICGUIDOF(KSDATAFORMAT_TYPE_AUDIO), STATICGUIDOF(KSDATAFORMAT_SUBTYPE_PCM),
      STATICGUIDOF(KSDATAFORMAT_SPECIFIER_WAVEFORMATEX) },
    2, 16, 16, 44100, 48000
};
static PKSDATARANGE HomePodCastStreamRanges[] =
{
    PKSDATARANGE(&HomePodCastRange), PKSDATARANGE(&PinDataRangeAttributeList)
};
static KSDATARANGE HomePodCastBridgeRange =
{
    sizeof(KSDATARANGE), 0, 0, 0,
    STATICGUIDOF(KSDATAFORMAT_TYPE_AUDIO), STATICGUIDOF(KSDATAFORMAT_SUBTYPE_ANALOG),
    STATICGUIDOF(KSDATAFORMAT_SPECIFIER_NONE)
};
static PKSDATARANGE HomePodCastBridgeRanges[] = { &HomePodCastBridgeRange };
static PCPIN_DESCRIPTOR HomePodCastPins[] =
{
    // Exactly one kernel render stream; shared clients are mixed by Windows.
    { 1, 1, 0, NULL,
      { 0, NULL, 0, NULL, SIZEOF_ARRAY(HomePodCastStreamRanges), HomePodCastStreamRanges,
        KSPIN_DATAFLOW_IN, KSPIN_COMMUNICATION_SINK, &KSCATEGORY_AUDIO, NULL, 0 } },
    { 0, 0, 0, NULL,
      { 0, NULL, 0, NULL, SIZEOF_ARRAY(HomePodCastBridgeRanges), HomePodCastBridgeRanges,
        KSPIN_DATAFLOW_OUT, KSPIN_COMMUNICATION_NONE, &KSCATEGORY_AUDIO, NULL, 0 } }
};
static PCCONNECTION_DESCRIPTOR HomePodCastConnections[] =
{
    { PCFILTER_NODE, 0, PCFILTER_NODE, 1 }
};
static PCPROPERTY_ITEM HomePodCastProperties[] =
{
    { &KSPROPSETID_Pin, KSPROPERTY_PIN_PROPOSEDATAFORMAT,
      KSPROPERTY_TYPE_SET | KSPROPERTY_TYPE_BASICSUPPORT, PropertyHandler_WaveFilter },
    { &KSPROPSETID_Pin, KSPROPERTY_PIN_PROPOSEDATAFORMAT2,
      KSPROPERTY_TYPE_GET | KSPROPERTY_TYPE_BASICSUPPORT, PropertyHandler_WaveFilter }
};
DEFINE_PCAUTOMATION_TABLE_PROP(HomePodCastAutomation, HomePodCastProperties);
static PCFILTER_DESCRIPTOR HomePodCastWaveDescriptor =
{
    0, &HomePodCastAutomation,
    sizeof(PCPIN_DESCRIPTOR), SIZEOF_ARRAY(HomePodCastPins), HomePodCastPins,
    sizeof(PCNODE_DESCRIPTOR), 0, NULL,
    SIZEOF_ARRAY(HomePodCastConnections), HomePodCastConnections, 0, NULL
};
