using System.Collections.Generic;
using System.Text;

namespace DribbleToSchool.Coop.Net
{
    /// <summary>
    /// Reads the events the native Bluetooth plugins pack for the game (Plugins/iOS/DTSCoopBLE.mm and
    /// Plugins/Android/DtsCoopBle.java write the same layout), once a frame, many at a time. Each event:
    /// [type u8][peer i32][state u8][rssi i16][address: u16 length + UTF-8][data: u16 length + bytes][name: u16 length + UTF-8].
    /// A Found event's data is the beacon from an Android host's scan response, its name the advertised local name of an
    /// iOS host; whichever holds a beacon is read (<see cref="RoomBeacon"/>). Pure C#, tested offline.
    /// </summary>
    public static class NativeEvents
    {
        /// <summary>Appends every whole event in <paramref name="count"/> bytes of <paramref name="buffer"/> to <paramref name="into"/>.</summary>
        public static void Decode(byte[] buffer, int count, List<LinkEvent> into)
        {
            if (buffer == null) return;
            var r = new ByteReader(buffer, 0, count);
            while (r.Remaining > 0)
            {
                var type = (LinkEventType)r.U8();
                int peer = r.I32();
                var state = (RadioState)r.U8();
                int rssi = r.I16();
                string address = Utf8(r.Raw(r.U16()));
                byte[] data = r.Raw(r.U16());
                string name = Utf8(r.Raw(r.U16()));
                if (r.Failed) return;   // a cut-off event: nothing more to read

                var e = new LinkEvent { type = type, peer = peer, state = state, rssi = rssi, address = address };
                switch (type)
                {
                    case LinkEventType.Found:
                        RoomBeacon beacon;
                        if (data.Length >= RoomBeacon.FixedBytes && RoomBeacon.TryParse(data, out beacon)) e.beacon = beacon;
                        else if (RoomBeacon.TryParseLocalName(name, out beacon)) e.beacon = beacon;
                        else continue;   // advertises the service, but no lobby we can read
                        break;
                    case LinkEventType.Data:
                        e.data = data;
                        break;
                    case LinkEventType.HostFailed:
                    case LinkEventType.ConnectFailed:
                        e.error = name;
                        break;
                }
                into.Add(e);
            }
        }

        static string Utf8(byte[] b)
        {
            if (b == null || b.Length == 0) return "";
            try { return Encoding.UTF8.GetString(b); }
            catch (System.Exception) { return ""; }
        }

        /// <summary>Packs one event the way the plugins do (for the tests and the editor).</summary>
        public static void Encode(ByteWriter w, LinkEvent e, byte[] data, string name)
        {
            w.U8((byte)e.type);
            w.I32(e.peer);
            w.U8((byte)e.state);
            w.I16(e.rssi);
            var a = Encoding.UTF8.GetBytes(e.address ?? "");
            w.U16(a.Length); w.Raw(a, 0, a.Length);
            data = data ?? new byte[0];
            w.U16(data.Length); w.Raw(data, 0, data.Length);
            var n = Encoding.UTF8.GetBytes(name ?? "");
            w.U16(n.Length); w.Raw(n, 0, n.Length);
        }
    }
}
