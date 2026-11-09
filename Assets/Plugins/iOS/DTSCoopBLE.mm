// Bluetooth LE for the co-op mode (called from Coop/Transport/IosBleLink.cs; Android's twin is
// Plugins/Android/DtsCoopBle.java, and both speak the same packed events, docs/COOP.md "Native bridge").
//
// The host is a GATT server (CBPeripheralManager) that advertises the game's service; each other player is a
// central (CBCentralManager) that connects, subscribes to the host's "to client" characteristic and writes to its
// "to host" one. Packets wait in a queue per player and go out as fast as CoreBluetooth takes them, the players served
// in turn; a queue that grows too long (a phone that stopped listening) loses its oldest whole messages, never part of
// one (the framing's first-packet flag, Coop/Net/CoopFraming.cs, marks where a message starts). Everything runs on one
// serial queue; the game polls the events once a frame.
//
// Every hosting run and every connection attempt has a number the game hands over (its generation), written into the
// state byte of each event about it, so the game can drop a late event of a run or connection it has already left
// (Coop/Net/LinkEventFilter.cs).
#if !__has_feature(objc_arc)
#error "DTSCoopBLE.mm is written for ARC: compile it with -fobjc-arc (Editor/IosPostBuild.cs sets this)."
#endif

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

/// How many packets may wait for one player before its oldest whole messages are dropped (the session repeats or
/// supersedes everything it sends). More than the longest message (2048 bytes in 19-byte pieces).
static const NSUInteger kDTSQueueLimit = 128;
/// How many events may wait for the game (it stopped polling: a scene loading, the app paused). Past this, the oldest
/// scan reports go first, then the oldest whole messages; the events that change a connection are always kept.
static const NSUInteger kDTSEventLimit = 8192;
/// A connection attempt that hasn't reached "subscribed" by then has failed.
static const double kDTSConnectTimeout = 10.0;
/// Advertising that fails after the lobby was announced is tried again after 1, 2, 4, then every 8 seconds.
static const double kDTSAdvertiseRetryMax = 8.0;
/// Hosting that hasn't started advertising this long after Bluetooth was ready has failed.
static const double kDTSHostTimeout = 8.0;

/// The framing's first-packet flag (Coop/Net/CoopFraming.cs).
static BOOL DTSIsFirstPacket(NSData *packet)
{
    return packet.length > 0 && (((const uint8_t *)packet.bytes)[0] & 0x40) != 0;
}

/// Too much waiting: drop the oldest whole messages until the queue fits (a message cut short at the front, part of it
/// already sent, goes too: the other end throws away a message whose end never comes).
static void DTSTrimQueue(NSMutableArray<NSData *> *queue, NSUInteger limit)
{
    while (queue.count > limit)
    {
        [queue removeObjectAtIndex:0];
        while (queue.count > 0 && !DTSIsFirstPacket(queue[0])) [queue removeObjectAtIndex:0];
    }
}

/// One packed event waiting for the game, with what the queue's trimming needs to know about it.
@interface DTSEvent : NSObject
@property (nonatomic, strong) NSData *bytes;
@property (nonatomic) int type;
@property (nonatomic) int peer;
@property (nonatomic) BOOL firstPacket;
@end

@implementation DTSEvent
@end

@interface DTSCoopBLE : NSObject <CBPeripheralManagerDelegate, CBCentralManagerDelegate, CBPeripheralDelegate>
@end

@implementation DTSCoopBLE
{
    dispatch_queue_t _queue;
    CBPeripheralManager *_pm;
    CBCentralManager *_cm;
    NSObject *_lock;
    NSMutableArray<DTSEvent *> *_events;   // under _lock
    int _radio;
    int _maxPacket;

    // Host
    BOOL _hostWanted, _hostAnnounced;
    int _hostGen;
    CBMutableService *_service;            // the service being added or added (nil: none)
    BOOL _serviceAdded;
    CBMutableCharacteristic *_toClient, *_toHost;
    NSString *_localName;
    int _startsInFlight;                    // startAdvertising calls CoreBluetooth hasn't answered yet...
    int _staleStarts;                       // ...and of those, how many belong to a run that has ended
    BOOL _readvertise;                      // start advertising again once the start in flight has answered
    double _advertiseRetry;
    int _advertiseToken;
    NSMutableDictionary<NSUUID *, NSNumber *> *_peerOf;
    NSMutableSet<NSUUID *> *_subscribed;
    NSMutableDictionary<NSNumber *, CBCentral *> *_centrals;
    NSMutableSet<NSUUID *> *_kicked;
    int _nextPeer;                          // never reused while the app runs
    NSMutableDictionary<NSNumber *, NSMutableArray<NSData *> *> *_outboxes;
    NSUInteger _turn;

    // Scanning and the client role
    BOOL _scanWanted;
    NSMutableDictionary<NSString *, CBPeripheral *> *_seen;
    NSMutableDictionary<NSString *, NSNumber *> *_lastReport;
    CBPeripheral *_host;
    CBCharacteristic *_hostWrite;
    BOOL _hostReady, _connectWaiting;
    int _connectGen;
    int _connectToken;
    NSMutableSet<NSUUID *> *_cancelling;    // connections hung up on whose end CoreBluetooth hasn't confirmed yet
    NSMutableArray<NSData *> *_writeQueue;
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
        _subscribed = [[NSMutableSet alloc] init];
        _outboxes = [[NSMutableDictionary alloc] init];
        _seen = [[NSMutableDictionary alloc] init];
        _lastReport = [[NSMutableDictionary alloc] init];
        _cancelling = [[NSMutableSet alloc] init];
        _writeQueue = [[NSMutableArray alloc] init];
        _nextPeer = 1;
        _maxPacket = 20;
        _radio = DTSRadioUnknown;
        // Back from the background: scanning and advertising may have been stopped meanwhile.
        [[NSNotificationCenter defaultCenter] addObserverForName:UIApplicationDidBecomeActiveNotification object:nil
                                                           queue:nil usingBlock:^(NSNotification *note) {
            dispatch_async(self->_queue, ^{ [self resume]; });
        }];
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
    uint8_t s = (uint8_t)(state & 0xFF);
    [e appendBytes:&s length:1];
    DTSPutU16(e, rssi & 0xFFFF);
    NSData *a = [(address ?: @"") dataUsingEncoding:NSUTF8StringEncoding] ?: [NSData data];
    if (a.length > 0xFFFF) a = [a subdataWithRange:NSMakeRange(0, 0xFFFF)];
    DTSPutU16(e, (int)a.length); [e appendData:a];
    NSData *body = data ?: [NSData data];
    if (body.length > 0xFFFF) body = [body subdataWithRange:NSMakeRange(0, 0xFFFF)];
    DTSPutU16(e, (int)body.length); [e appendData:body];
    NSData *n = [(name ?: @"") dataUsingEncoding:NSUTF8StringEncoding] ?: [NSData data];
    if (n.length > 0xFFFF) n = [n subdataWithRange:NSMakeRange(0, 0xFFFF)];
    DTSPutU16(e, (int)n.length); [e appendData:n];

    DTSEvent *ev = [[DTSEvent alloc] init];
    ev.bytes = e;
    ev.type = type;
    ev.peer = peer;
    ev.firstPacket = type == DTSEvData && DTSIsFirstPacket(body);
    @synchronized (_lock)
    {
        if (_events.count >= kDTSEventLimit && ![self makeRoomFor:ev]) return;
        [_events addObject:ev];
    }
}

/// The game has stopped polling and the queue is full (under _lock): make room by dropping the oldest scan report, or
/// else the oldest whole message. The events that change a connection are never dropped. False: drop the new one.
- (BOOL)makeRoomFor:(DTSEvent *)ev
{
    if (ev.type == DTSEvFound) return NO;
    for (NSUInteger i = 0; i < _events.count; i++)
        if (_events[i].type == DTSEvFound) { [_events removeObjectAtIndex:i]; return YES; }
    for (NSUInteger i = 0; i < _events.count; i++)
    {
        if (_events[i].type != DTSEvData) continue;
        int peer = _events[i].peer;
        [_events removeObjectAtIndex:i];
        // ...and the rest of that message, up to the next one's start
        while (i < _events.count)
        {
            DTSEvent *next = _events[i];
            if (next.type == DTSEvData && next.peer == peer)
            {
                if (next.firstPacket) break;
                [_events removeObjectAtIndex:i];
            }
            else i++;
        }
        return YES;
    }
    return ev.type != DTSEvData;
}

- (void)emit:(int)type peer:(int)peer gen:(int)gen
{
    [self emit:type peer:peer state:gen rssi:0 address:nil data:nil name:nil];
}

- (int)pollInto:(unsigned char *)buffer capacity:(int)capacity
{
    int used = 0;
    @synchronized (_lock)
    {
        NSUInteger taken = 0;
        while (taken < _events.count)
        {
            NSData *e = _events[taken].bytes;
            if (used + (int)e.length > capacity) break;
            memcpy(buffer + used, e.bytes, e.length);
            used += (int)e.length;
            taken++;
        }
        if (taken > 0) [_events removeObjectsInRange:NSMakeRange(0, taken)];
    }
    return used;
}

// ---------- Radio state ----------

- (void)start
{
    dispatch_async(_queue, ^{
        if (self->_cm == nil)
            // (the central asks iOS to offer switching Bluetooth on, once, when it is off as the co-op screen opens)
            self->_cm = [[CBCentralManager alloc] initWithDelegate:self queue:self->_queue options:@{ CBCentralManagerOptionShowPowerAlertKey: @YES }];
        if (self->_pm == nil)
            self->_pm = [[CBPeripheralManager alloc] initWithDelegate:self queue:self->_queue options:@{ CBPeripheralManagerOptionShowPowerAlertKey: @NO }];
        // A new link on the C# side starts from "unknown": tell it what the radio is now, and the packet size.
        if (self->_radio != DTSRadioUnknown) [self emit:DTSEvRadio peer:0 state:self->_radio rssi:0 address:nil data:nil name:nil];
        [self emit:DTSEvPacketSize peer:0 state:0 rssi:self->_maxPacket address:nil data:nil name:nil];
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

- (BOOL)centralOn { return _cm != nil && _cm.state == CBManagerStatePoweredOn; }
- (BOOL)peripheralOn { return _pm != nil && _pm.state == CBManagerStatePoweredOn; }

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
    for (NSNumber *peer in _centrals.allKeys) [self emit:DTSEvDisconnected peer:peer.intValue gen:_hostGen];
    [_centrals removeAllObjects];
    [_peerOf removeAllObjects];
    [_subscribed removeAllObjects];
    [_outboxes removeAllObjects];
    _service = nil;        // CoreBluetooth drops published services with the power: publish again when it is back
    _serviceAdded = NO;
    _startsInFlight = _staleStarts = 0;   // (nothing in flight survives the power going)
    _readvertise = NO;
    _advertiseToken++;
    [_seen removeAllObjects];
    [_lastReport removeAllObjects];
    [_cancelling removeAllObjects];
    if (_host != nil)
    {
        BOOL wasReady = _hostReady;
        [self forgetHost];
        [self emit:(wasReady ? DTSEvDisconnected : DTSEvConnectFailed) peer:0 state:_connectGen rssi:0 address:nil data:nil name:@"off"];
    }
    _connectWaiting = NO;
    [self updatePacketSize];
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

/// The app is active again: scanning and advertising pick up where they were.
- (void)resume
{
    if (_scanWanted && [self centralOn]) [self beginScan];
    if (_hostWanted && _serviceAdded && [self peripheralOn]) [self advertise];
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

- (void)startHostWithName:(NSString *)name gen:(int)gen
{
    dispatch_async(_queue, ^{
        if (self->_hostWanted) [self endHost];   // (a new run: the old one's players and service go)
        self->_hostWanted = YES;
        self->_hostAnnounced = NO;
        self->_hostGen = gen;
        self->_localName = name;
        self->_advertiseRetry = 1.0;
        if ([self peripheralOn]) [self beginHost];
        else if (self->_pm != nil && self->_pm.state != CBManagerStateUnknown && self->_pm.state != CBManagerStateResetting)
        {
            // Off, unauthorized or unsupported: no lobby can start now.
            self->_hostWanted = NO;
            [self emit:DTSEvHostFailed peer:0 state:gen rssi:0 address:nil data:nil name:@"off"];
        }
    });
}

- (void)beginHost
{
    if (_service == nil)
    {
        // To client: notify only. To host: write without response only. (Nothing to read: the host only ever pushes.)
        _toClient = [[CBMutableCharacteristic alloc] initWithType:[CBUUID UUIDWithString:kDTSToClient]
                                                       properties:CBCharacteristicPropertyNotify
                                                            value:nil permissions:CBAttributePermissionsReadable];
        _toHost = [[CBMutableCharacteristic alloc] initWithType:[CBUUID UUIDWithString:kDTSToHost]
                                                     properties:CBCharacteristicPropertyWriteWithoutResponse
                                                          value:nil permissions:CBAttributePermissionsWriteable];
        _service = [[CBMutableService alloc] initWithType:[CBUUID UUIDWithString:kDTSService] primary:YES];
        _service.characteristics = @[ _toClient, _toHost ];
        _serviceAdded = NO;
        [_pm removeAllServices];
        [_pm addService:_service];
        if (!_hostAnnounced)
        {
            int gen = _hostGen;
            dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(kDTSHostTimeout * NSEC_PER_SEC)), _queue, ^{
                if (self->_hostGen == gen && self->_hostWanted && !self->_hostAnnounced) [self hostTrouble:@"timeout"];
            });
        }
        return;
    }
    if (_serviceAdded) [self advertise];
}

- (void)peripheralManager:(CBPeripheralManager *)peripheral didAddService:(CBService *)service error:(NSError *)error
{
    if (service != _service)
    {
        // A service of a run that has ended (or been replaced) finished adding late: take it down again.
        if (error == nil && [self peripheralOn]) [_pm removeService:(CBMutableService *)service];
        return;
    }
    if (error != nil)
    {
        _service = nil;
        [self hostTrouble:error.localizedDescription];
        return;
    }
    _serviceAdded = YES;
    if (_hostWanted) [self advertise];
}

/// Hosting went wrong. Before the lobby was announced the game is told (it can't start); after, the players already in
/// it stay connected, and advertising is tried again with a growing pause so latecomers can still find the lobby.
- (void)hostTrouble:(NSString *)why
{
    if (!_hostWanted) return;
    if (!_hostAnnounced)
    {
        [self endHost];
        _hostWanted = NO;
        [self emit:DTSEvHostFailed peer:0 state:_hostGen rssi:0 address:nil data:nil name:why ?: @"failed"];
        return;
    }
    int token = ++_advertiseToken;
    double wait = _advertiseRetry;
    _advertiseRetry = MIN(kDTSAdvertiseRetryMax, _advertiseRetry * 2);
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(wait * NSEC_PER_SEC)), _queue, ^{
        if (token != self->_advertiseToken || !self->_hostWanted || ![self peripheralOn]) return;
        [self beginHost];
    });
}

- (void)advertise
{
    if (![self peripheralOn]) return;
    if (_startsInFlight > 0)
    {
        // A start is on its way: start again (with the new name) once it has answered.
        _readvertise = YES;
        return;
    }
    if (_pm.isAdvertising) [_pm stopAdvertising];
    NSMutableDictionary *ad = [[NSMutableDictionary alloc] init];
    ad[CBAdvertisementDataServiceUUIDsKey] = @[ [CBUUID UUIDWithString:kDTSService] ];
    // (eight characters: what fits beside a 128-bit service UUID in iOS's advertisement; Coop/Net/RoomBeacon.cs)
    if (_localName.length > 0) ad[CBAdvertisementDataLocalNameKey] = _localName;
    _startsInFlight++;
    _readvertise = NO;
    [_pm startAdvertising:ad];
}

- (void)peripheralManagerDidStartAdvertising:(CBPeripheralManager *)peripheral error:(NSError *)error
{
    if (_startsInFlight > 0) _startsInFlight--;
    if (_staleStarts > 0 || !_hostWanted)
    {
        // The answer to a start of a run that has ended: whatever it started is not this run's.
        if (_staleStarts > 0) _staleStarts--;
        if ([self peripheralOn]) [_pm stopAdvertising];
        if (_hostWanted && _serviceAdded) [self advertise];   // (the run now on was waiting for this answer)
        return;
    }
    BOOL already = error != nil && [error.domain isEqualToString:CBErrorDomain] && error.code == CBErrorAlreadyAdvertising;
    if (error != nil && !already)
    {
        [self hostTrouble:error.localizedDescription];
        return;
    }
    _advertiseRetry = 1.0;
    if (!_hostAnnounced)
    {
        _hostAnnounced = YES;
        [self emit:DTSEvHostStarted peer:0 gen:_hostGen];
    }
    if (_readvertise) [self advertise];   // (the name changed meanwhile)
}

- (void)updateBeaconName:(NSString *)name
{
    dispatch_async(_queue, ^{
        if ([name isEqualToString:self->_localName]) return;
        self->_localName = name;
        if (self->_hostWanted && self->_serviceAdded) [self advertise];
    });
}

/// Ends the hosting run: no advertisement, no service, no players (no events: the game asked).
- (void)endHost
{
    _advertiseToken++;
    _staleStarts = _startsInFlight;   // (their answers are not the next run's)
    _readvertise = NO;
    if ([self peripheralOn])
    {
        [_pm stopAdvertising];   // (also when a start is still on its way)
        [_pm removeAllServices];
    }
    _service = nil;
    _serviceAdded = NO;
    _toClient = _toHost = nil;
    [_centrals removeAllObjects];
    [_peerOf removeAllObjects];
    [_kicked removeAllObjects];
    [_subscribed removeAllObjects];
    [_outboxes removeAllObjects];
    [self updatePacketSize];
}

- (void)stopHost
{
    dispatch_async(_queue, ^{
        self->_hostWanted = NO;
        self->_hostAnnounced = NO;
        [self endHost];
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
        [self->_outboxes removeObjectForKey:@(peer)];
        [self updatePacketSize];
    });
}

- (int)peerFor:(CBCentral *)central
{
    NSNumber *known = _peerOf[central.identifier];
    if (known != nil) return known.intValue;
    if ([_kicked containsObject:central.identifier]) return 0;
    int peer = _nextPeer++;
    _peerOf[central.identifier] = @(peer);
    _centrals[@(peer)] = central;
    [_pm setDesiredConnectionLatency:CBPeripheralManagerConnectionLatencyLow forCentral:central];
    [self emit:DTSEvConnected peer:peer gen:_hostGen];
    [self updatePacketSize];
    return peer;
}

- (void)forgetCentral:(NSUUID *)identifier
{
    NSNumber *known = _peerOf[identifier];
    if (known == nil) return;
    [_centrals removeObjectForKey:known];
    [_peerOf removeObjectForKey:identifier];
    [_outboxes removeObjectForKey:known];
    [self emit:DTSEvDisconnected peer:known.intValue gen:_hostGen];
    [self updatePacketSize];
}

- (void)peripheralManager:(CBPeripheralManager *)peripheral central:(CBCentral *)central didSubscribeToCharacteristic:(CBCharacteristic *)characteristic
{
    if (characteristic != _toClient || !_hostWanted) return;   // (an old run's characteristic)
    [_kicked removeObject:central.identifier];   // a new subscription: a new connection (a kicked phone may come back)
    // Subscribed again without having unsubscribed: the phone reconnected without CoreBluetooth saying it had gone. The
    // old connection is over, and this is a new one. (A phone that wrote before subscribing keeps its number.)
    if ([_subscribed containsObject:central.identifier]) [self forgetCentral:central.identifier];
    [_subscribed addObject:central.identifier];
    [self peerFor:central];
}

- (void)peripheralManager:(CBPeripheralManager *)peripheral central:(CBCentral *)central didUnsubscribeFromCharacteristic:(CBCharacteristic *)characteristic
{
    if (characteristic != _toClient) return;
    [_kicked removeObject:central.identifier];
    [_subscribed removeObject:central.identifier];
    [self forgetCentral:central.identifier];
}

- (void)peripheralManager:(CBPeripheralManager *)peripheral didReceiveWriteRequests:(NSArray<CBATTRequest *> *)requests
{
    for (CBATTRequest *request in requests)
    {
        if (request.characteristic != _toHost || request.value == nil || !_hostWanted) continue;
        // (a phone that writes before it subscribes is a player all the same)
        int peer = [self peerFor:request.central];
        if (peer == 0) continue;   // kicked
        [self emit:DTSEvData peer:peer state:_hostGen rssi:0 address:nil data:[request.value copy] name:nil];
    }
    if (requests.count > 0) [peripheral respondToRequest:requests[0] withResult:CBATTErrorSuccess];
}

- (void)queueToPeer:(int)peer data:(NSData *)data
{
    if (_centrals[@(peer)] == nil) return;
    NSMutableArray<NSData *> *queue = _outboxes[@(peer)];
    if (queue == nil)
    {
        queue = [[NSMutableArray alloc] init];
        _outboxes[@(peer)] = queue;
    }
    [queue addObject:data];
    DTSTrimQueue(queue, kDTSQueueLimit);
    [self pumpOutbox];
}

/// Sends what the players' queues hold, one packet per player in turn, until CoreBluetooth's own queue is full (it says
/// when it has room again: peripheralManagerIsReadyToUpdateSubscribers).
- (void)pumpOutbox
{
    if (_toClient == nil || ![self peripheralOn]) return;
    while (_outboxes.count > 0)
    {
        NSArray<NSNumber *> *peers = [_outboxes.allKeys sortedArrayUsingSelector:@selector(compare:)];
        NSUInteger count = peers.count;
        for (NSUInteger i = 0; i < count; i++)
        {
            NSNumber *peer = peers[(_turn + i) % count];
            NSMutableArray<NSData *> *queue = _outboxes[peer];
            CBCentral *central = _centrals[peer];
            if (central == nil || queue.count == 0) { [_outboxes removeObjectForKey:peer]; continue; }
            if (![_pm updateValue:queue[0] forCharacteristic:_toClient onSubscribedCentrals:@[ central ]])
            {
                _turn = (_turn + i) % count;   // (this player goes first when there is room again)
                return;
            }
            [queue removeObjectAtIndex:0];
            if (queue.count == 0) [_outboxes removeObjectForKey:peer];
        }
        _turn++;
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
        if ([self centralOn]) [self beginScan];
    });
}

- (void)beginScan
{
    // (asked again even when already scanning: iOS may have stopped it while the app was away, and asking again while
    // it runs only renews it)
    [_cm scanForPeripheralsWithServices:@[ [CBUUID UUIDWithString:kDTSService] ] options:@{ CBCentralManagerScanOptionAllowDuplicatesKey: @YES }];
}

- (void)stopScan
{
    dispatch_async(_queue, ^{
        self->_scanWanted = NO;
        if ([self centralOn]) [self->_cm stopScan];
    });
}

- (void)centralManager:(CBCentralManager *)central didDiscoverPeripheral:(CBPeripheral *)peripheral
     advertisementData:(NSDictionary<NSString *, id> *)advertisementData RSSI:(NSNumber *)RSSI
{
    NSString *address = peripheral.identifier.UUIDString;
    _seen[address] = peripheral;
    NSString *name = advertisementData[CBAdvertisementDataLocalNameKey];
    NSDictionary *serviceData = advertisementData[CBAdvertisementDataServiceDataKey];
    NSData *beacon = [serviceData isKindOfClass:[NSDictionary class]] ? serviceData[[CBUUID UUIDWithString:kDTSBeaconKey]] : nil;
    if (![name isKindOfClass:[NSString class]]) name = nil;
    if (![beacon isKindOfClass:[NSData class]]) beacon = nil;
    // A report with no lobby in it (an Android host's advertisement before its scan response arrives) says nothing:
    // it mustn't use up the report that does.
    if (beacon.length == 0 && name.length == 0) return;
    double now = CFAbsoluteTimeGetCurrent();
    NSNumber *last = _lastReport[address];
    if (last != nil && now - last.doubleValue < 0.25) return;   // a few reports a second are plenty
    _lastReport[address] = @(now);
    int rssi = RSSI.intValue == 127 ? -100 : RSSI.intValue;
    [self emit:DTSEvFound peer:0 state:0 rssi:rssi address:address data:beacon name:name];
}

// ---------- Client ----------

- (void)connect:(NSString *)address gen:(int)gen
{
    dispatch_async(_queue, ^{
        [self dropHost];
        self->_connectGen = gen;
        CBPeripheral *p = self->_seen[address];
        if (p == nil && [self centralOn])
        {
            NSUUID *uuid = [[NSUUID alloc] initWithUUIDString:address];
            if (uuid != nil) p = [self->_cm retrievePeripheralsWithIdentifiers:@[ uuid ]].firstObject;
        }
        if (p == nil || ![self centralOn])
        {
            [self emit:DTSEvConnectFailed peer:0 state:gen rssi:0 address:address data:nil name:@"unknown"];
            return;
        }
        self->_host = p;
        self->_hostReady = NO;
        p.delegate = self;
        int token = ++self->_connectToken;
        if ([self->_cancelling containsObject:p.identifier])
        {
            // The last connection to this host is still being hung up: connecting now would have its end read as this
            // attempt failing. Connect once it has ended (or after a moment, should CoreBluetooth never say).
            self->_connectWaiting = YES;
            dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1.5 * NSEC_PER_SEC)), self->_queue, ^{
                if (self->_connectToken != token || !self->_connectWaiting || self->_host != p) return;
                [self->_cancelling removeObject:p.identifier];
                [self beginConnect];
            });
        }
        else [self beginConnect];
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(kDTSConnectTimeout * NSEC_PER_SEC)), self->_queue, ^{
            if (self->_connectToken != token || self->_hostReady || self->_host != p) return;
            [self dropHost];
            [self emit:DTSEvConnectFailed peer:0 state:gen rssi:0 address:address data:nil name:@"timeout"];
        });
    });
}

- (void)beginConnect
{
    _connectWaiting = NO;
    if (_host == nil || ![self centralOn]) return;
    [_cm connectPeripheral:_host options:nil];
}

/// Client state back to "no host" (no events).
- (void)forgetHost
{
    _host = nil;
    _hostReady = NO;
    _hostWrite = nil;
    _connectWaiting = NO;
    _connectToken++;
    [_writeQueue removeAllObjects];
}

/// Hang up on the host without telling the game (it asked, or the attempt is over).
- (void)dropHost
{
    if (_host == nil) return;
    CBPeripheral *p = _host;
    [self forgetHost];
    if ([self centralOn] && (p.state == CBPeripheralStateConnected || p.state == CBPeripheralStateConnecting))
    {
        [_cancelling addObject:p.identifier];
        [_cm cancelPeripheralConnection:p];
    }
    [self updatePacketSize];
}

- (void)disconnect
{
    dispatch_async(_queue, ^{ [self dropHost]; });
}

/// A connection we hung up on has ended. True when that is what this callback was about (nothing more to do).
- (BOOL)cancelled:(CBPeripheral *)peripheral
{
    if (![_cancelling containsObject:peripheral.identifier]) return NO;
    [_cancelling removeObject:peripheral.identifier];
    if (_host == peripheral && _connectWaiting) [self beginConnect];
    return YES;
}

- (void)centralManager:(CBCentralManager *)central didConnectPeripheral:(CBPeripheral *)peripheral
{
    if (peripheral != _host || _connectWaiting) return;
    [peripheral discoverServices:@[ [CBUUID UUIDWithString:kDTSService] ]];
}

- (void)centralManager:(CBCentralManager *)central didFailToConnectPeripheral:(CBPeripheral *)peripheral error:(NSError *)error
{
    if ([self cancelled:peripheral] || peripheral != _host) return;
    [self forgetHost];
    [self emit:DTSEvConnectFailed peer:0 state:_connectGen rssi:0 address:nil data:nil name:error.localizedDescription ?: @"failed"];
    [self updatePacketSize];
}

- (void)centralManager:(CBCentralManager *)central didDisconnectPeripheral:(CBPeripheral *)peripheral error:(NSError *)error
{
    if ([self cancelled:peripheral] || peripheral != _host) return;
    BOOL wasReady = _hostReady;
    [self forgetHost];
    [self emit:(wasReady ? DTSEvDisconnected : DTSEvConnectFailed) peer:0 state:_connectGen rssi:0 address:nil data:nil name:@"lost"];
    [self updatePacketSize];
}

/// The connection is no good (no service, a refused subscription, the host took its service down): hang up. Before the
/// game heard "connected" that is a failed attempt; after, a lost connection.
- (void)fail:(CBPeripheral *)peripheral why:(NSString *)why
{
    if (peripheral != _host) return;
    BOOL wasReady = _hostReady;
    [self dropHost];
    [self emit:(wasReady ? DTSEvDisconnected : DTSEvConnectFailed) peer:0 state:_connectGen rssi:0 address:nil data:nil name:why];
}

- (void)peripheral:(CBPeripheral *)peripheral didDiscoverServices:(NSError *)error
{
    if (peripheral != _host) return;
    if (error == nil)
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
    CBCharacteristic *notify = nil, *write = nil;
    if (error == nil)
        for (CBCharacteristic *c in service.characteristics)
        {
            if ([c.UUID isEqual:[CBUUID UUIDWithString:kDTSToHost]]) write = c;
            if ([c.UUID isEqual:[CBUUID UUIDWithString:kDTSToClient]]) notify = c;
        }
    if (notify == nil || write == nil) { [self fail:peripheral why:@"no characteristics"]; return; }
    _hostWrite = write;
    [peripheral setNotifyValue:YES forCharacteristic:notify];
}

- (void)peripheral:(CBPeripheral *)peripheral didUpdateNotificationStateForCharacteristic:(CBCharacteristic *)characteristic error:(NSError *)error
{
    if (peripheral != _host) return;
    if (error != nil || !characteristic.isNotifying) { [self fail:peripheral why:@"subscribe"]; return; }
    if (_hostReady) return;
    _hostReady = YES;
    [self updatePacketSize];
    [self emit:DTSEvConnected peer:0 gen:_connectGen];
}

- (void)peripheral:(CBPeripheral *)peripheral didModifyServices:(NSArray<CBService *> *)invalidatedServices
{
    // The host took the game's service down (it stopped hosting, or its Bluetooth restarted): this connection is over.
    if (peripheral != _host) return;
    for (CBService *s in invalidatedServices)
        if ([s.UUID isEqual:[CBUUID UUIDWithString:kDTSService]]) { [self fail:peripheral why:@"service gone"]; return; }
}

- (void)peripheral:(CBPeripheral *)peripheral didUpdateValueForCharacteristic:(CBCharacteristic *)characteristic error:(NSError *)error
{
    if (peripheral != _host || !_hostReady || error != nil || characteristic.value == nil) return;
    [self emit:DTSEvData peer:0 state:_connectGen rssi:0 address:nil data:[characteristic.value copy] name:nil];
}

- (void)pumpWrites
{
    while (_writeQueue.count > 0 && _host != nil && _hostReady && _hostWrite != nil && _host.canSendWriteWithoutResponse)
    {
        [_host writeValue:_writeQueue[0] forCharacteristic:_hostWrite type:CBCharacteristicWriteWithoutResponse];
        [_writeQueue removeObjectAtIndex:0];
    }
}

- (void)peripheralIsReadyToSendWriteWithoutResponse:(CBPeripheral *)peripheral
{
    if (peripheral == _host) [self pumpWrites];
}

- (void)send:(int)peer data:(NSData *)data
{
    dispatch_async(_queue, ^{
        if (peer == 0)
        {
            if (self->_host == nil || !self->_hostReady) return;
            [self->_writeQueue addObject:data];
            DTSTrimQueue(self->_writeQueue, kDTSQueueLimit);
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

void DTSCoop_StartHost(const char *localName, int gen)
{
    [[DTSCoopBLE shared] startHostWithName:[NSString stringWithUTF8String:localName ?: ""] ?: @"" gen:gen];
}

void DTSCoop_UpdateBeacon(const char *localName)
{
    [[DTSCoopBLE shared] updateBeaconName:[NSString stringWithUTF8String:localName ?: ""] ?: @""];
}

void DTSCoop_StopHost(void) { [[DTSCoopBLE shared] stopHost]; }
void DTSCoop_Kick(int peer) { [[DTSCoopBLE shared] kick:peer]; }
void DTSCoop_StartScan(void) { [[DTSCoopBLE shared] startScan]; }
void DTSCoop_StopScan(void) { [[DTSCoopBLE shared] stopScan]; }

void DTSCoop_Connect(const char *address, int gen)
{
    [[DTSCoopBLE shared] connect:[NSString stringWithUTF8String:address ?: ""] ?: @"" gen:gen];
}

void DTSCoop_Disconnect(void) { [[DTSCoopBLE shared] disconnect]; }

void DTSCoop_Send(int peer, const unsigned char *data, int length)
{
    if (data == NULL || length <= 0) return;
    [[DTSCoopBLE shared] send:peer data:[NSData dataWithBytes:data length:(NSUInteger)length]];
}

int DTSCoop_Poll(unsigned char *buffer, int capacity)
{
    if (buffer == NULL || capacity <= 0) return 0;
    return [[DTSCoopBLE shared] pollInto:buffer capacity:capacity];
}

void DTSCoop_Shutdown(void) { [[DTSCoopBLE shared] shutdown]; }

void DTSCoop_OpenSettings(void)
{
    dispatch_async(dispatch_get_main_queue(), ^{
        NSURL *url = [NSURL URLWithString:UIApplicationOpenSettingsURLString];
        if (url != nil) [[UIApplication sharedApplication] openURL:url options:@{} completionHandler:nil];
    });
}

}
