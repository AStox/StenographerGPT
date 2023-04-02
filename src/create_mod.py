import sys
import cffi
import ctypes
import traceback

ffi = cffi.FFI()

ffi.cdef("""
typedef unsigned char Boolean;
typedef unsigned int UInt32;
typedef unsigned long long UInt64;
typedef int OSStatus;
typedef UInt64 AudioObjectID;
typedef UInt32 AudioDeviceID;
typedef UInt32 AudioObjectPropertySelector;
typedef UInt32 AudioObjectPropertyScope;
typedef UInt32 AudioObjectPropertyElement;
typedef UInt32 OSType;
typedef signed long long CFIndex;
typedef unsigned long CFHashCode;
typedef const void * CFStringRef;
typedef const void * CFAllocatorRef;
typedef ... *CFMutableArrayRef;
typedef ... *CFMutableDictionaryRef;
typedef ... *CFDictionaryRef;
typedef void *CFTypeRef;
typedef CFTypeRef CFArrayRef;

// Some of the required constants
#define kAudioHardwarePropertyDevices 1684370979
#define kAudioHardwarePropertyPlugInList 1634758755
#define kAudioHardwarePropertyPlugInForBundleID 1886683513
#define kAudioPlugInCreateAggregateDevice 1667326759
#define kAudioAggregateDevicePropertyFullSubDeviceList 1718775076
#define kAudioObjectPropertyScopeGlobal 1735159650
#define kAudioObjectPropertyElementMaster 0

// Define the structs
typedef struct {
    AudioObjectPropertySelector mSelector;
    AudioObjectPropertyScope mScope;
    AudioObjectPropertyElement mElement;
} AudioObjectPropertyAddress;

typedef struct {
    CFIndex version;
    void *retain;
    void *release;
    void *copyDescription;
    void *equal;
} CFArrayCallBacks;

typedef struct {
    CFIndex version;
    void *(*retain)(CFAllocatorRef allocator, const void *value);
    void (*release)(CFAllocatorRef allocator, const void *value);
    CFStringRef (*copyDescription)(const void *value);
    Boolean (*equal)(const void *value1, const void *value2);
    CFHashCode (*hash)(const void *value);
} CFDictionaryKeyCallBacks;

typedef struct {
    CFIndex version;
    void *(*retain)(CFAllocatorRef allocator, const void *value);
    void (*release)(CFAllocatorRef allocator, const void *value);
    CFStringRef (*copyDescription)(const void *value);
    Boolean (*equal)(const void *value1, const void *value2);
} CFDictionaryValueCallBacks;

static const AudioObjectID kAudioObjectSystemObject = 1;

// CoreFoundation/CFString.h
typedef UInt32 CFStringEncoding;
CFIndex CFStringGetLength(CFStringRef theString);
Boolean CFStringGetCString(CFStringRef theString, char *buffer, CFIndex bufferSize, CFStringEncoding encoding);
CFIndex CFStringGetMaximumSizeForEncoding(CFIndex length, CFStringEncoding encoding);


// CoreFoundation
const void *CFSTR(const char *cStr);
CFStringRef CFStringCreateWithCString(CFAllocatorRef alloc, const char *cStr, CFStringEncoding encoding);
CFMutableArrayRef CFArrayCreateMutable(CFAllocatorRef, CFIndex,const CFArrayCallBacks *);
CFArrayRef CFArrayCreate(CFAllocatorRef allocator, const void **values, CFIndex numValues, const CFArrayCallBacks *callBacks);
CFMutableDictionaryRef CFDictionaryCreateMutable(CFAllocatorRef, CFIndex, const CFDictionaryKeyCallBacks *, const CFDictionaryValueCallBacks *);
void CFDictionarySetValue(CFMutableDictionaryRef theDict, const void *key, const void *value);
OSStatus AudioHardwareCreateAggregateDevice(CFDictionaryRef inDescription, AudioDeviceID *outDevice);


// Define the functions
Boolean AudioObjectHasProperty(AudioObjectID inObjectID, const AudioObjectPropertyAddress* inAddress);
OSStatus AudioObjectGetPropertyDataSize(AudioObjectID inObjectID, const AudioObjectPropertyAddress* inAddress, UInt32 inQualifierDataSize, const void* inQualifierData, UInt32* outDataSize);
OSStatus AudioObjectGetPropertyData(AudioObjectID inObjectID, const AudioObjectPropertyAddress* inAddress, UInt32 inQualifierDataSize, const void* inQualifierData, UInt32* ioDataSize, void* outData);
OSStatus AudioObjectSetPropertyData(AudioObjectID inObjectID, const AudioObjectPropertyAddress* inAddress, UInt32 inQualifierDataSize, const void* inQualifierData, UInt32 inDataSize, const void* inData);

typedef struct AudioComponentDescription {
    OSType componentType;
    OSType componentSubType;
    OSType componentManufacturer;
    UInt32 componentFlags;
    UInt32 componentFlagsMask;
} AudioComponentDescription;

typedef void *AudioComponent;
typedef AudioComponent (*AudioComponentFindNextFn)(AudioComponent, const AudioComponentDescription *);
typedef OSStatus (*AudioComponentGetDescriptionFn)(AudioComponent, AudioComponentDescription *);

AudioComponent AudioComponentFindNext(AudioComponent inComponent, const AudioComponentDescription *inDesc);
OSStatus AudioComponentGetDescription(AudioComponent inComponent, AudioComponentDescription *outDesc);





typedef struct AudioValueTranslation {
    const void *mInputData;
    UInt32 mInputDataSize;
    void *mOutputData;
    UInt32 mOutputDataSize;
} AudioValueTranslation;


enum {
    kAudioObjectSystemObject = 1,
    kAudioObjectPropertyScopeGlobal = 0x676C6F62,
};
typedef uint32_t CFOptionFlags;
typedef int32_t CFComparisonResult;
enum {
    kCFCompareLessThan = -1,
    kCFCompareEqualTo = 0,
    kCFCompareGreaterThan = 1
};

void CFRelease(CFTypeRef cf);

CFComparisonResult CFStringCompare(
    CFStringRef theString1,
    CFStringRef theString2,
    CFOptionFlags compareOptions
);

""")

# _cac = ffi.dlopen(None)  # Load the default system library
# _cf = ffi.dlopen("/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation")


# _ca = ctypes.CDLL('/System/Library/Frameworks/CoreAudio.framework/Versions/A/CoreAudio')
_cac = ffi.dlopen('/System/Library/Frameworks/CoreAudio.framework/Versions/A/CoreAudio')

kAudioObjectPropertyScopeGlobal = 0
kAudioObjectPropertyElementMaster = 0
kCFStringEncodingUTF8 = 0x08000100

class _CoreAudio:
    @staticmethod
    def get_property(target, selector, data_type):
        print("-------- Getting property --------")
        print(f"Target: {target}, Selector: {selector}, Data type: {data_type}")
        address = ffi.new("AudioObjectPropertyAddress *")
        address[0].mSelector = selector
        address[0].mScope = _cac.kAudioObjectPropertyScopeGlobal
        address[0].mElement = _cac.kAudioObjectPropertyElementMaster

        has_prop = _cac.AudioObjectHasProperty(target, address)
        print(f"Has property: {has_prop}")
        if not has_prop:
            return None

        size = ffi.new("UInt32 *")
        err = _cac.AudioObjectGetPropertyDataSize(target, address, 0, ffi.NULL, size)
        print(f"GetPropertyDataSize err: {err}, size: {size[0]}")
        if err != 0:
            return None

        data = ffi.new(f"{data_type}[]", size[0] // ffi.sizeof(data_type))
        err = _cac.AudioObjectGetPropertyData(
            target, 
            address, 
            0, 
            ffi.NULL, 
            size, 
            data
        )
        print(f"GetPropertyData err: {err}, data: {data}")
        if err != 0:
            return None

        return data

    @staticmethod
    def set_property(target, selector, prop_data, scope=kAudioObjectPropertyScopeGlobal):
        prop = ffi.new("AudioObjectPropertyAddress*", {'mSelector': selector, 'mScope': scope, 'mElement': kAudioObjectPropertyElementMaster})
        err = _cac.AudioObjectSetPropertyData(target, prop, 0, ffi.NULL, ffi.sizeof(ffi.typeof(prop_data).item.cname), prop_data)
        assert err == 0, "Can't set Core Audio property data"

    
    @staticmethod
    def CFString_to_str(cfstr):
        print("Converting CFString to str...")
        str_length = _cac.CFStringGetLength(cfstr)
        max_size = _cac.CFStringGetMaximumSizeForEncoding(str_length, kCFStringEncodingUTF8) + 1
        str_buffer = ffi.new('char[]', max_size)

        success = _cac.CFStringGetCString(cfstr, str_buffer, max_size, kCFStringEncodingUTF8)
        if success:
            return ffi.string(str_buffer).decode()
        else:
            raise ValueError("Could not decode CFStringRef")




    
    @staticmethod
    def create_multi_output_device(device_uids):
        print("Creating multi-output device...")
        kAudioHardwareCreateAggregateDevice = int.from_bytes(b'cagg', byteorder='big')
        kAudioDevicePropertyDeviceUID = int.from_bytes(b'duid', byteorder='big')

        kAudioHardwarePropertyPlugInForBundleID = int.from_bytes(b'pibi', byteorder='big')

        # print("******** Getting plugin bundle ref...")
        # plugin_bundle_ref = _CoreAudio.get_property(_cac.kAudioObjectSystemObject, kAudioHardwarePropertyPlugInForBundleID, "CFStringRef")
        # print(f"plugin_bundle_ref: {plugin_bundle_ref}")
        # qualifier_data = ffi.new("struct { CFStringRef mBundleID; } *", (plugin_bundle_ref,))
        # plugin_id = ffi.new("AudioObjectID *")

        # err = _cac.AudioObjectGetPropertyData(
        #     _cac.kAudioObjectSystemObject,
        #     ffi.new("AudioObjectPropertyAddress *", [_cac.kAudioHardwarePropertyPlugInForBundleID, _cac.kAudioObjectPropertyScopeGlobal, _cac.kAudioObjectPropertyElementMaster]),
        #     ffi.sizeof(qualifier_data[0]),
        #     qualifier_data,
        #     ffi.sizeof(plugin_id),
        #     plugin_id
        # )

        # plugin_id = _CoreAudio.get_plugins()[0]
        kAudioUnitType_Output = int.from_bytes(b'auou', byteorder='big')
        kAudioUnitSubType_MultiChannelMixer = int.from_bytes(b'mcmx', byteorder='big')
        plugin_id = _CoreAudio.get_plugins()
        print(f"plugin_id: {plugin_id} (type: {type(plugin_id)})")

        devices_array = ffi.new("CFStringRef[]", len(device_uids))
        for i, device_uid in enumerate(device_uids):
            devices_array[i] = _cac.CFStringCreateWithCString(ffi.NULL, device_uid.encode(), kCFStringEncodingUTF8)

        devices_cfarray = _cac.CFArrayCreate(ffi.NULL, ffi.cast("const void**", devices_array), len(device_uids), ffi.NULL)

        subdevices = ffi.new("CFMutableDictionaryRef *")
        subdevices[0] = _cac.CFDictionaryCreateMutable(ffi.NULL, 1, ffi.NULL, ffi.NULL)
        _cac.CFDictionarySetValue(subdevices[0], ffi.cast("const void *", _cac.CFStringCreateWithCString(ffi.NULL, b"SubDevices", 0)), ffi.cast("const void *", devices_cfarray))

        new_device_id = ffi.new("AudioDeviceID *")
        address = ffi.new("AudioObjectPropertyAddress *")
        address[0].mSelector = kAudioHardwareCreateAggregateDevice
        address[0].mScope = _cac.kAudioObjectPropertyScopeGlobal
        address[0].mElement = _cac.kAudioObjectPropertyElementMaster

        # plugin_id = _CoreAudio.get_property(_cac.kAudioObjectSystemObject, _cac.kAudioHardwarePropertyPlugInForBundleID, "AudioObjectID")

        plugin_id = ffi.cast("AudioObjectID", plugin_id)

        new_device_id = ffi.new('unsigned int *')

        print("        ------------------               ")
        print(f"plugin_id: {plugin_id} (type: {type(plugin_id)})")
        print(f"address: {ffi.addressof(address[0])} (type: {type(ffi.addressof(address[0]))})")
        print(f"subdevices size: {ffi.cast('UInt32', ffi.sizeof(subdevices))} (type: {type(ffi.cast('UInt32', ffi.sizeof(subdevices)))})")
        print(f"subdevices: {subdevices} (type: {type(subdevices)})")
        print(f"ffi.sizeof(new_device_id): {ffi.cast('UInt32 *', ffi.sizeof(new_device_id))} (type: {type(ffi.cast('UInt32 *', ffi.sizeof(new_device_id)))})")
        print(f"new_device_id: {new_device_id} (type: {type(new_device_id)})")
        print("        ------------------               ")

        err = _cac.AudioObjectGetPropertyData(
            plugin_id,                                       # AudioObjectID inObjectID
            address,                                         # const AudioObjectPropertyAddress* inAddress
            ffi.sizeof(subdevices),                          # UInt32 inQualifierDataSize
            subdevices,                                      # const void* inQualifierData
            ffi.cast("UInt32 *", ffi.addressof(ffi.new("UInt32[]", [ffi.sizeof(new_device_id)]))),   # UInt32* ioDataSize
            new_device_id                                    # void* outData
        )
        print("ok")
        if err != 0:
            print(f"Error code: {err}")
            return None


        return new_device_id[0]

    def get_plugins():
        print("-------- get plugins --------")
        kAudioHardwarePropertyPlugInList = int.from_bytes(b'plg#', byteorder='big')
        kAudioPlugInPropertyBundleID = int.from_bytes(b'bid#', byteorder='big')

        num_plugins = ffi.new("UInt32 *")
        address = ffi.new("AudioObjectPropertyAddress *", [kAudioHardwarePropertyPlugInList, _cac.kAudioObjectPropertyScopeGlobal, _cac.kAudioObjectPropertyElementMaster])
        _cac.AudioObjectGetPropertyDataSize(_cac.kAudioObjectSystemObject, address, 0, ffi.NULL, num_plugins)

        plugins_data_size = num_plugins[0] * ffi.sizeof("UInt64")
        plugins = ffi.new("UInt64[]", num_plugins[0])

        _cac.AudioObjectGetPropertyData(_cac.kAudioObjectSystemObject, address, 0, ffi.NULL, num_plugins, plugins)

        address = ffi.new("AudioObjectPropertyAddress *", [kAudioPlugInPropertyBundleID, _cac.kAudioObjectPropertyScopeGlobal, _cac.kAudioObjectPropertyElementMaster])

        for i in range(num_plugins[0]):
            print("Plugin:", i)
            plugin_id = plugins[i]

            bundle_id = ffi.new("CFStringRef *")
            size = ffi.new("UInt32 *", ffi.sizeof(bundle_id))

            err = _cac.AudioObjectGetPropertyData(plugin_id, address, 0, ffi.NULL, size, bundle_id)

            if err == 0 and bundle_id[0] != ffi.NULL:
                compare_options = ffi.new("CFOptionFlags *", 0)
                result = _cac.CFStringCompare(bundle_id[0], _cac.CFStringCreateWithCString(ffi.NULL, b"com.apple.audio.aggregate-devices", 0), compare_options[0])

                if result == _cac.kCFCompareEqualTo:
                    print("Found Aggregate Device Plugin")
                    _cac.CFRelease(bundle_id[0])
                    return plugin_id

                _cac.CFRelease(bundle_id[0])

        return None



    @staticmethod
    def get_plugin():
        kAudioHardwarePropertyPlugInForBundleID = _cac.kAudioHardwarePropertyPlugInForBundleID
        kAudioObjectPropertyScopeGlobal = _cac.kAudioObjectPropertyScopeGlobal
        kAudioObjectPropertyElementMaster = _cac.kAudioObjectPropertyElementMaster
        kAudioObjectSystemObject = _cac.kAudioObjectSystemObject

        property_address = ffi.new("AudioObjectPropertyAddress *", [kAudioHardwarePropertyPlugInForBundleID, kAudioObjectPropertyScopeGlobal, kAudioObjectPropertyElementMaster])

        data_size = ffi.new("UInt32 *")
        status = _cac.AudioObjectGetPropertyDataSize(kAudioObjectSystemObject, property_address, 0, ffi.NULL, data_size)
        if status != 0:
            print(f"Error getting data size: {status}")
            sys.exit(-1)

        translation = ffi.new("AudioValueTranslation *")
        bundle_id = _cac.CFSTR("com.apple.audio.CoreAudioPluginAggregate")
        translation.mInputData = bundle_id
        translation.mInputDataSize = ffi.sizeof("CFStringRef")
        translation.mOutputData = ffi.NULL
        translation.mOutputDataSize = 0

        status = _cac.AudioObjectGetPropertyData(kAudioObjectSystemObject, property_address, ffi.sizeof(translation[0]), translation, data_size, translation)
        if status != 0:
            print(f"Error getting plugin ID: {status}")
            sys.exit(-1)

        plugin_id = ffi.cast("AudioObjectID *", translation.mOutputData)[0]
        print(f"Plugin ID: {plugin_id}")


def main():
    # Get the system object
    system_object = _cac.kAudioObjectSystemObject
    print(f"Getting devices for system object {system_object}...")

    # Get the list of available devices
    kAudioHardwarePropertyDevices = _cac.kAudioHardwarePropertyDevices

    device_ids = _CoreAudio.get_property(system_object, kAudioHardwarePropertyDevices, "AudioDeviceID")
    kAudioObjectPropertyName = int.from_bytes(b'lnam', byteorder='big')
    for device_id in device_ids:
        uid = _CoreAudio.get_property(device_id, kAudioObjectPropertyName, "CFStringRef")
        uid_str = _CoreAudio.CFString_to_str(uid[0])
        print(f"Device ID: {device_id}, UID: {uid_str}")

    device_uids = []
    for device_id in device_ids:
        uid = _CoreAudio.get_property(device_id, kAudioObjectPropertyName, "CFStringRef")
        uid_str = _CoreAudio.CFString_to_str(uid[0])
        device_uids.append(uid_str)

    new_device_id = _CoreAudio.create_multi_output_device(device_uids)
    print(f"Created new Multi-Output device with ID {new_device_id}")

if __name__ == "__main__":
    main()
