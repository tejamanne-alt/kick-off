// Bluetooth LE for the co-op mode (called from Coop/Transport/IosBleLink.cs; Android's twin is
// Plugins/Android/DtsCoopBle.java, and both speak the same packed events, docs/COOP.md "Native bridge").
//
// The host is a GATT server (CBPeripheralManager) that advertises the game's service; each other player is a
// central (CBCentralManager) that connects, subscribes to the host's "to client" characteristic and writes to its
// "to host" one. Packets are queued and sent as fast as CoreBluetooth takes them, so none are dropped while a
// connection lasts. Everything runs on one serial queue; the game polls the events once a frame.
#import <Foundation/Foundation.h>
#import <CoreBluetooth/CoreBluetooth.h>
#import <UIKit/UIKit.h>

static NSString *const kDTSService  = @"8C5F0001-2B7E-4D5A-9E3B-4B4F32C0FFEE";
static NSString *const kDTSToClient = @"8C5F0002-2B7E-4D5A-9E3B-4B4F32C0FFEE";
static NSString *const kDTSToHost   = @"8C5F0003-2B7E-4D5A-9E3B-4B4F32C0FFEE";
// The 16-bit key an Android host's scan response carries the lobby's beacon under.
static NSString *const kDTSBeaconKey = @"4B4F";

enum { DTSEvRadio = 1, DTSEvFound = 2, DTSEvConnected = 3, DTSEvDisconnected = 4, DTSEvData = 5,
       DTSEvHostStarted = 6, DTSEvHostFailed = 7, DTSEvConnectFailed = 8, DTSEvPacketSize = 9 };
enum { DTSRadioUnknown = 0, DTSRadioUnsupported = 1, DTSRadioUnauthorized = 2, DTSRadioOff = 3, DTSRadioOn = 4 };

/// How many packets may wait for one player before the oldest whole messages are dropped (the session repeats them).
static const NSUInteger kDTSQueueLimit = 96;

@interface DTSCoopBLE : NSObject <CBPeripheralManagerDelegate, CBCentralManagerDelegate, CBPeripheralDelegate>
@end

@implementation DTSCoopBLE
{
    dispatch_queue_t _queue;
    CBPeripheralManager *_pm;
    CBCentralManager *_cm;
    NSObject *_lock;
    NSMutableArray<NSData *> *_events;   // packed records, under _lock
    volatile int _radio;
    volatile int _maxPacket;

    // Host
    BOOL _hostWanted, _serviceAdded, _advertising, _hostAnnounced;
    CBMutableService *_service;
    CBMutableCharacteristic *_toClient, *_toHost;
    NSString *_localName;
    NSMutableDictionary<NSUUID *, NSNumber *> *_peerOf;
    NSMutableDictionary<NSNumber *, CBCentral *> *_centrals;
    NSMutableSet<NSUUID *> *_kicked;
    int _nextPeer;
    NSMutableArray<NSArray *> *_outbox;   // @[peer, data]

    // Scanning and the client role
    BOOL _scanWanted, _scanning;
    NSMutableDictionary<NSString *, CBPeripheral *> *_seen;
    NSMutableDictionary<NSString *, NSNumber *> *_lastReport;
    CBPeripheral *_host;
    CBCharacteristic *_hostWrite;
    BOOL _hostReady, _explicitDisconnect;
    NSMutableArray<NSData *> *_writeQueue;
    int _connectToken;
}

+ (instancetype)shared
{
    static DTSCoopBLE *instance;
    static dispatch_once_t once;
    dispatch_once(&once, ^{ instance = [[DTSCoopBLE alloc] init]; });
    return instance;
}

- (instancetype)init
{
    if ((self = [super init]))
    {
        _queue = dispatch_queue_create("com.dribbletoschool.coop.ble", DISPATCH_QUEUE_SERIAL);
        _lock = [[NSObject alloc] init];
        _events = [[NSMutableArray alloc] init];
        _peerOf = [[NSMutableDictionary alloc] init];
        _centrals = [[NSMutableDictionary alloc] init];
        _kicked = [[NSMutableSet alloc] init];
        _outbox = [[NSMutableArray alloc] init];
        _seen = [[NSMutableDictionary alloc] init];
        _lastReport = [[NSMutableDictionary alloc] init];
        _writeQueue = [[NSMutableArray alloc] init];
        _nextPeer = 1;
        _maxPacket = 20;
        _radio = DTSRadioUnknown;
    }
    return self;
}

// ---------- Events (packed for the game: docs/COOP.md "Native bridge") ----------

static void DTSPutU16(NSMutableData *d, int v) { uint8_t b[2] = { (uint8_t)(v & 0xFF), (uint8_t)((v >> 8) & 0xFF) }; [d appendBytes:b length:2]; }

- (void)emit:(int)type peer:(int)peer state:(int)state rssi:(int)rssi address:(NSString *)address data:(NSData *)data name:(NSString *)name
{
    NSMutableData *e = [[NSMutableData alloc] init];
    uint8_t t = (uint8_t)type;
    [e appendBytes:&t length:1];
    uint8_t p[4] = { (uint8_t)(peer & 0xFF), (uint8_t)((peer >> 8) & 0xFF), (uint8_t)((peer >> 16) & 0xFF), (uint8_t)((peer >> 24) & 0xFF) };
    [e appendBytes:p length:4];
    uint8_t s = (uint8_t)state;
    [e appendBytes:&s length:1];
    DTSPutU16(e, rssi & 0xFFFF);
    NSData *a = [(address ?: @"") dataUsingEncoding:NSUTF8StringEncoding];
    DTSPutU16(e, (int)MIN(a.length, 0xFFFFu)); [e appendData:a];
    NSData *body = data ?: [NSData data];
    DTSPutU16(e, (int)MIN(body.length, 0xFFFFu)); [e appendData:body];
    NSData *n = [(name ?: @"") dataUsingEncoding:NSUTF8StringEncoding];
    DTSPutU16(e, (int)MIN(n.length, 0xFFFFu)); [e appendData:n];
    @synchronized (_lock) { [_events addObject:e]; }
}

- (void)emit:(int)type peer:(int)peer
{
    [self emit:type peer:peer state:0 rssi:0 address:nil data:nil name:nil];
}

- (int)pollInto:(unsigned char *)buffer capacity:(int)capacity
{
    int used = 0;
    @synchronized (_lock)
    {
        while (_events.count > 0)
        {
            NSData *e = _events[0];
            if (used + (int)e.length > capacity) break;
            memcpy(buffer + used, e.bytes, e.length);
            used += (int)e.length;
            [_events removeObjectAtIndex:0];
        }
    }
    return used;
}

// ---------- Radio state ----------

- (void)start
{
    dispatch_async(_queue, ^{
        if (self->_cm == nil)
            self->_cm = [[CBCentralManager alloc] initWithDelegate:self queue:self->_queue options:@{ CBCentralManagerOptionShowPowerAlertKey: @NO }];
        if (self->_pm == nil)
            self->_pm = [[CBPeripheralManager alloc] initWithDelegate:self queue:self->_queue options:@{ CBPeripheralManagerOptionShowPowerAlertKey: @NO }];
    });
}

static int DTSRadioOf(CBManagerState s)
{
    switch (s)
    {
        case CBManagerStatePoweredOn: return DTSRadioOn;
        case CBManagerStatePoweredOff: return DTSRadioOff;
        case CBManagerStateUnauthorized: return DTSRadioUnauthorized;
        case CBManagerStateUnsupported: return DTSRadioUnsupported;
        default: return DTSRadioUnknown;
    }
}

- (void)refreshRadio
{
    int c = _cm != nil ? DTSRadioOf(_cm.state) : DTSRadioUnknown;
    int p = _pm != nil ? DTSRadioOf(_pm.state) : DTSRadioUnknown;
    int r = c;
    if (c == DTSRadioUnauthorized || p == DTSRadioUnauthorized) r = DTSRadioUnauthorized;
    else if (c == DTSRadioUnsupported) r = DTSRadioUnsupported;
    else if (c == DTSRadioOn && p != DTSRadioOn && p != DTSRadioUnknown) r = p;
    if (r == _radio) return;
    int before = _radio;
    _radio = r;
    [self emit:DTSEvRadio peer:0 state:r rssi:0 address:nil data:nil name:nil];
    if (before == DTSRadioOn && r != DTSRadioOn) [self radioLost];
}

/// Bluetooth went off: every connection is gone (CoreBluetooth does not always say so one by one).
- (void)radioLost
{
    for (NSNumber *peer in _centrals.allKeys) [self emit:DTSEvDisconnected peer:peer.intValue];
    [_centrals removeAllObjects];
    [_peerOf removeAllObjects];
    [_outbox removeAllObjects];
    _service = nil;        // CoreBluetooth drops published services with the power: publish again when it is back
    _serviceAdded = NO;
    _advertising = NO;
    _scanning = NO;
    if (_host != nil)
    {
        BOOL wasReady = _hostReady;
        _host = nil;
        _hostReady = NO;
        _hostWrite = nil;
        [_writeQueue removeAllObjects];
        if (!_explicitDisconnect) [self emit:(wasReady ? DTSEvDisconnected : DTSEvConnectFailed) peer:0];
    }
}

- (void)centralManagerDidUpdateState:(CBCentralManager *)central
{
    [self refreshRadio];
    if (central.state == CBManagerStatePoweredOn && _scanWanted) [self beginScan];
}

- (void)peripheralManagerDidUpdateState:(CBPeripheralManager *)peripheral
{
    [self refreshRadio];
    if (peripheral.state == CBManagerStatePoweredOn && _hostWanted) [self beginHost];
}

- (void)updatePacketSize
{
    int size = 512;
    if (_host != nil && _hostReady) size = MIN(size, (int)[_host maximumWriteValueLengthForType:CBCharacteristicWriteWithoutResponse]);
    for (CBCentral *c in _centrals.allValues) size = MIN(size, (int)c.maximumUpdateValueLength);
    size = MAX(20, size);
    if (size != _maxPacket)
    {
        _maxPacket = size;
        [self emit:DTSEvPacketSize peer:0 state:0 rssi:size address:nil data:nil name:nil];
    }
}

// ---------- Host ----------

- (void)startHostWithName:(NSString *)name
{
    dispatch_async(_queue, ^{
        self->_hostWanted = YES;
        self->_hostAnnounced = NO;
        self->_localName = name;
        if (self->_pm.state == CBManagerStatePoweredOn) [self beginHost];
    });
}

- (void)beginHost
{
    if (!_serviceAdded && _service == nil)
    {
        _toClient = [[CBMutableCharacteristic alloc] initWithType:[CBUUID UUIDWithString:kDTSToClient]
                                                       properties:CBCharacteristicPropertyNotify | CBCharacteristicPropertyRead
                                                            value:nil permissions:CBAttributePermissionsReadable];
        _toHost = [[CBMutableCharacteristic alloc] initWithType:[CBUUID UUIDWithString:kDTSToHost]
                                                     properties:CBCharacteristicPropertyWrite | CBCharacteristicPropertyWriteWithoutResponse
                                                          value:nil permissions:CBAttributePermissionsWriteable];
        _service = [[CBMutableService alloc] initWithType:[CBUUID UUIDWithString:kDTSService] primary:YES];
        _service.characteristics = @[ _toClient, _toHost ];
        [_pm removeAllServices];
        [_pm addService:_service];
        return;
    }
    if (_serviceAdded) [self advertise];
}

- (void)peripheralManager:(CBPeripheralManager *)peripheral didAddService:(CBService *)service error:(NSError *)error
{
    if (error != nil)
    {
        _service = nil;
        [self emit:DTSEvHostFailed peer:0 state:0 rssi:0 address:nil data:nil name:error.localizedDescription];
        return;
    }
    _serviceAdded = YES;
    if (_hostWanted) [self advertise];
}

- (void)advertise
{
    if (_pm.isAdvertising) [_pm stopAdvertising];
    NSMutableDictionary *ad = [[NSMutableDictionary alloc] init];
    ad[CBAdvertisementDataServiceUUIDsKey] = @[ [CBUUID UUIDWithString:kDTSService] ];
    if (_localName.length > 0) ad[CBAdvertisementDataLocalNameKey] = _localName;
    [_pm startAdvertising:ad];
}

- (void)peripheralManagerDidStartAdvertising:(CBPeripheralManager *)peripheral error:(NSError *)error
{
    if (error != nil)
    {
        _advertising = NO;
        [self emit:DTSEvHostFailed peer:0 state:0 rssi:0 address:nil data:nil name:error.localizedDescription];
        return;
    }
    _advertising = YES;
    if (!_hostAnnounced)
    {
        _hostAnnounced = YES;
        [self emit:DTSEvHostStarted peer:0];
    }
}

- (void)updateBeaconName:(NSString *)name
{
    dispatch_async(_queue, ^{
        if ([name isEqualToString:self->_localName]) return;
        self->_localName = name;
        if (self->_hostWanted && self->_serviceAdded && self->_pm.state == CBManagerStatePoweredOn) [self advertise];
    });
}

- (void)stopHost
{
    dispatch_async(_queue, ^{
        self->_hostWanted = NO;
        if (self->_pm.isAdvertising) [self->_pm stopAdvertising];
        [self->_pm removeAllServices];
        self->_service = nil;
        self->_serviceAdded = NO;
        self->_advertising = NO;
        [self->_centrals removeAllObjects];
        [self->_peerOf removeAllObjects];
        [self->_kicked removeAllObjects];
        [self->_outbox removeAllObjects];
        [self updatePacketSize];
    });
}

- (void)kick:(int)peer
{
    // A peripheral can't hang up on a central: forget it, so it hears nothing more and times out.
    dispatch_async(_queue, ^{
        CBCentral *c = self->_centrals[@(peer)];
        if (c == nil) return;
        [self->_kicked addObject:c.identifier];
        [self->_centrals removeObjectForKey:@(peer)];
        [self->_peerOf removeObjectForKey:c.identifier];
    });
}

- (int)peerFor:(CBCentral *)central announce:(BOOL)announce
{
    NSNumber *known = _peerOf[central.identifier];
    if (known != nil) return known.intValue;
    if ([_kicked containsObject:central.identifier]) return 0;
    int peer = _nextPeer++;
    _peerOf[central.identifier] = @(peer);
    _centrals[@(peer)] = central;
    [_pm setDesiredConnectionLatency:CBPeripheralManagerConnectionLatencyLow forCentral:central];
    if (announce) [self emit:DTSEvConnected peer:peer];
    [self updatePacketSize];
    return peer;
}

- (void)peripheralManager:(CBPeripheralManager *)peripheral central:(CBCentral *)central didSubscribeToCharacteristic:(CBCharacteristic *)characteristic
{
    [_kicked removeObject:central.identifier];   // a new subscription: a new connection (a kicked phone may come back)
    [self peerFor:central announce:YES];        // (already known if it wrote first: nothing more to say)
}

- (void)peripheralManager:(CBPeripheralManager *)peripheral central:(CBCentral *)central didUnsubscribeFromCharacteristic:(CBCharacteristic *)characteristic
{
    NSNumber *known = _peerOf[central.identifier];
    [_kicked removeObject:central.identifier];
    if (known == nil) return;
    [_centrals removeObjectForKey:known];
    [_peerOf removeObjectForKey:central.identifier];
    [self emit:DTSEvDisconnected peer:known.intValue];
    [self updatePacketSize];
}

- (void)peripheralManager:(CBPeripheralManager *)peripheral didReceiveWriteRequests:(NSArray<CBATTRequest *> *)requests
{
    for (CBATTRequest *request in requests)
    {
        if (![request.characteristic.UUID isEqual:[CBUUID UUIDWithString:kDTSToHost]] || request.value == nil) continue;
        int peer = [self peerFor:request.central announce:YES];
        if (peer == 0) continue;   // kicked
        [self emit:DTSEvData peer:peer state:0 rssi:0 address:nil data:[request.value copy] name:nil];
    }
    if (requests.count > 0) [peripheral respondToRequest:requests[0] withResult:CBATTErrorSuccess];
}

- (void)queueToPeer:(int)peer data:(NSData *)data
{
    [_outbox addObject:@[ @(peer), data ]];
    [self trimOutbox];
    [self pumpOutbox];
}

/// Too much waiting (a player whose phone has stopped listening): drop the oldest whole messages (the framing's last-packet flag ends one).
- (void)trimOutbox
{
    while (_outbox.count > kDTSQueueLimit)
    {
        while (_outbox.count > 0)
        {
            NSData *packet = _outbox[0][1];
            [_outbox removeObjectAtIndex:0];
            if (packet.length > 0 && (((const uint8_t *)packet.bytes)[0] & 0x80) != 0) break;
        }
    }
}

- (void)pumpOutbox
{
    while (_outbox.count > 0)
    {
        NSArray *item = _outbox[0];
        CBCentral *central = _centrals[item[0]];
        if (central == nil) { [_outbox removeObjectAtIndex:0]; continue; }
        if (![_pm updateValue:item[1] forCharacteristic:_toClient onSubscribedCentrals:@[ central ]]) return;   // full: wait for ready
        [_outbox removeObjectAtIndex:0];
    }
}

- (void)peripheralManagerIsReadyToUpdateSubscribers:(CBPeripheralManager *)peripheral
{
    [self pumpOutbox];
}

// ---------- Scanning ----------

- (void)startScan
{
    dispatch_async(_queue, ^{
        self->_scanWanted = YES;
        if (self->_cm.state == CBManagerStatePoweredOn) [self beginScan];
    });
}

- (void)beginScan
{
    if (_scanning) return;
    _scanning = YES;
    [_cm scanForPeripheralsWithServices:@[ [CBUUID UUIDWithString:kDTSService] ] options:@{ CBCentralManagerScanOptionAllowDuplicatesKey: @YES }];
}

- (void)stopScan
{
    dispatch_async(_queue, ^{
        self->_scanWanted = NO;
        if (self->_scanning && self->_cm.state == CBManagerStatePoweredOn) [self->_cm stopScan];
        self->_scanning = NO;
    });
}

- (void)centralManager:(CBCentralManager *)central didDiscoverPeripheral:(CBPeripheral *)peripheral
     advertisementData:(NSDictionary<NSString *, id> *)advertisementData RSSI:(NSNumber *)RSSI
{
    NSString *address = peripheral.identifier.UUIDString;
    _seen[address] = peripheral;
    double now = CFAbsoluteTimeGetCurrent();
    NSNumber *last = _lastReport[address];
    if (last != nil && now - last.doubleValue < 0.25) return;   // a few reports a second are plenty
    _lastReport[address] = @(now);
    NSString *name = advertisementData[CBAdvertisementDataLocalNameKey];
    NSDictionary *serviceData = advertisementData[CBAdvertisementDataServiceDataKey];
    NSData *beacon = serviceData[[CBUUID UUIDWithString:kDTSBeaconKey]];
    int rssi = RSSI.intValue == 127 ? -100 : RSSI.intValue;
    [self emit:DTSEvFound peer:0 state:0 rssi:rssi address:address data:beacon name:name];
}

// ---------- Client ----------

- (void)connect:(NSString *)address
{
    dispatch_async(_queue, ^{
        [self dropHost];
        CBPeripheral *p = self->_seen[address];
        if (p == nil)
        {
            NSUUID *uuid = [[NSUUID alloc] initWithUUIDString:address];
            if (uuid != nil) p = [self->_cm retrievePeripheralsWithIdentifiers:@[ uuid ]].firstObject;
        }
        if (p == nil || self->_cm.state != CBManagerStatePoweredOn)
        {
            [self emit:DTSEvConnectFailed peer:0 state:0 rssi:0 address:address data:nil name:@"unknown"];
            return;
        }
        self->_host = p;
        self->_hostReady = NO;
        self->_explicitDisconnect = NO;
        p.delegate = self;
        int token = ++self->_connectToken;
        [self->_cm connectPeripheral:p options:nil];
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(10 * NSEC_PER_SEC)), self->_queue, ^{
            if (self->_connectToken != token || self->_hostReady || self->_host != p) return;
            self->_explicitDisconnect = YES;
            [self->_cm cancelPeripheralConnection:p];
            self->_host = nil;
            [self emit:DTSEvConnectFailed peer:0 state:0 rssi:0 address:address data:nil name:@"timeout"];
        });
    });
}

/// Hang up on the host without telling the game (it asked).
- (void)dropHost
{
    if (_host == nil) return;
    _explicitDisconnect = YES;
    [_cm cancelPeripheralConnection:_host];
    _host = nil;
    _hostReady = NO;
    _hostWrite = nil;
    [_writeQueue removeAllObjects];
    [self updatePacketSize];
}

- (void)disconnect
{
    dispatch_async(_queue, ^{ [self dropHost]; });
}

- (void)centralManager:(CBCentralManager *)central didConnectPeripheral:(CBPeripheral *)peripheral
{
    if (peripheral != _host) return;
    [peripheral discoverServices:@[ [CBUUID UUIDWithString:kDTSService] ]];
}

- (void)centralManager:(CBCentralManager *)central didFailToConnectPeripheral:(CBPeripheral *)peripheral error:(NSError *)error
{
    if (peripheral != _host) return;
    _host = nil;
    if (!_explicitDisconnect) [self emit:DTSEvConnectFailed peer:0 state:0 rssi:0 address:nil data:nil name:error.localizedDescription];
}

- (void)centralManager:(CBCentralManager *)central didDisconnectPeripheral:(CBPeripheral *)peripheral error:(NSError *)error
{
    if (peripheral != _host) return;
    BOOL wasReady = _hostReady;
    _host = nil;
    _hostReady = NO;
    _hostWrite = nil;
    [_writeQueue removeAllObjects];
    if (!_explicitDisconnect) [self emit:(wasReady ? DTSEvDisconnected : DTSEvConnectFailed) peer:0];
    [self updatePacketSize];
}

- (void)fail:(CBPeripheral *)peripheral why:(NSString *)why
{
    _explicitDisconnect = YES;
    [_cm cancelPeripheralConnection:peripheral];
    _host = nil;
    [self emit:DTSEvConnectFailed peer:0 state:0 rssi:0 address:nil data:nil name:why];
}

- (void)peripheral:(CBPeripheral *)peripheral didDiscoverServices:(NSError *)error
{
    if (peripheral != _host) return;
    for (CBService *s in peripheral.services)
        if ([s.UUID isEqual:[CBUUID UUIDWithString:kDTSService]])
        {
            [peripheral discoverCharacteristics:@[ [CBUUID UUIDWithString:kDTSToClient], [CBUUID UUIDWithString:kDTSToHost] ] forService:s];
            return;
        }
    [self fail:peripheral why:@"no service"];
}

- (void)peripheral:(CBPeripheral *)peripheral didDiscoverCharacteristicsForService:(CBService *)service error:(NSError *)error
{
    if (peripheral != _host) return;
    CBCharacteristic *notify = nil;
    for (CBCharacteristic *c in service.characteristics)
    {
        if ([c.UUID isEqual:[CBUUID UUIDWithString:kDTSToHost]]) _hostWrite = c;
        if ([c.UUID isEqual:[CBUUID UUIDWithString:kDTSToClient]]) notify = c;
    }
    if (notify == nil || _hostWrite == nil) { [self fail:peripheral why:@"no characteristics"]; return; }
    [peripheral setNotifyValue:YES forCharacteristic:notify];
}

- (void)peripheral:(CBPeripheral *)peripheral didUpdateNotificationStateForCharacteristic:(CBCharacteristic *)characteristic error:(NSError *)error
{
    if (peripheral != _host) return;
    if (error != nil || !characteristic.isNotifying) { [self fail:peripheral why:@"subscribe"]; return; }
    if (_hostReady) return;
    _hostReady = YES;
    [self updatePacketSize];
    [self emit:DTSEvConnected peer:0];
}

- (void)peripheral:(CBPeripheral *)peripheral didUpdateValueForCharacteristic:(CBCharacteristic *)characteristic error:(NSError *)error
{
    if (peripheral != _host || error != nil || characteristic.value == nil) return;
    [self emit:DTSEvData peer:0 state:0 rssi:0 address:nil data:[characteristic.value copy] name:nil];
}

- (void)pumpWrites
{
    while (_writeQueue.count > 0 && _host != nil && _hostWrite != nil && _host.canSendWriteWithoutResponse)
    {
        [_host writeValue:_writeQueue[0] forCharacteristic:_hostWrite type:CBCharacteristicWriteWithoutResponse];
        [_writeQueue removeObjectAtIndex:0];
    }
}

- (void)peripheralIsReadyToSendWriteWithoutResponse:(CBPeripheral *)peripheral
{
    [self pumpWrites];
}

- (void)send:(int)peer data:(NSData *)data
{
    dispatch_async(_queue, ^{
        if (peer == 0)
        {
            if (self->_host == nil || !self->_hostReady) return;
            [self->_writeQueue addObject:data];
            while (self->_writeQueue.count > kDTSQueueLimit) [self->_writeQueue removeObjectAtIndex:0];
            [self pumpWrites];
        }
        else [self queueToPeer:peer data:data];
    });
}

- (void)shutdown
{
    [self stopHost];
    [self stopScan];
    [self disconnect];
}

@end

// ---------- What C# calls (Coop/Transport/IosBleLink.cs) ----------

extern "C" {

void DTSCoop_Init(void) { [[DTSCoopBLE shared] start]; }

void DTSCoop_StartHost(const char *localName)
{
    [[DTSCoopBLE shared] startHostWithName:[NSString stringWithUTF8String:localName ?: ""]];
}

void DTSCoop_UpdateBeacon(const char *localName)
{
    [[DTSCoopBLE shared] updateBeaconName:[NSString stringWithUTF8String:localName ?: ""]];
}

void DTSCoop_StopHost(void) { [[DTSCoopBLE shared] stopHost]; }
void DTSCoop_Kick(int peer) { [[DTSCoopBLE shared] kick:peer]; }
void DTSCoop_StartScan(void) { [[DTSCoopBLE shared] startScan]; }
void DTSCoop_StopScan(void) { [[DTSCoopBLE shared] stopScan]; }

void DTSCoop_Connect(const char *address)
{
    [[DTSCoopBLE shared] connect:[NSString stringWithUTF8String:address ?: ""]];
}

void DTSCoop_Disconnect(void) { [[DTSCoopBLE shared] disconnect]; }

void DTSCoop_Send(int peer, const unsigned char *data, int length)
{
    if (data == NULL || length <= 0) return;
    [[DTSCoopBLE shared] send:peer data:[NSData dataWithBytes:data length:(NSUInteger)length]];
}

int DTSCoop_Poll(unsigned char *buffer, int capacity) { return [[DTSCoopBLE shared] pollInto:buffer capacity:capacity]; }
void DTSCoop_Shutdown(void) { [[DTSCoopBLE shared] shutdown]; }

void DTSCoop_OpenSettings(void)
{
    dispatch_async(dispatch_get_main_queue(), ^{
        NSURL *url = [NSURL URLWithString:UIApplicationOpenSettingsURLString];
        if (url != nil) [[UIApplication sharedApplication] openURL:url options:@{} completionHandler:nil];
    });
}

}
