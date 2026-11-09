using System;
using System.Collections.Generic;

namespace DribbleToSchool.Coop.Net
{
    /// <summary>
    /// Splits a message into radio packets and puts them back together. A Bluetooth LE write or notification carries at most
    /// the link's MTU less 3 bytes (20 on the oldest phones, 180 to 500 once the MTU is raised), and a message (the lobby's
    /// snapshot with four names) can be longer. Each packet starts with one byte: bit 7 set on the message's last packet,
    /// bit 6 on its first, bits 0-5 the message's number (mod 64). The native layers deliver a connection's packets in order,
    /// but a queue that overflows (a phone that stopped listening) drops its oldest messages, and a reconnection cuts one
    /// short: a message is only ever put together from its first packet to its last, all of one number, and anything else
    /// (a tail whose start was dropped) is thrown away, never read as a message of its own. Every message the session sends
    /// is repeated or superseded, so nothing is lost for good.
    /// </summary>
    public static class CoopFraming
    {
        public const int HeaderBytes = 1;
        /// <summary>The smallest payload a packet can have (BLE's default MTU of 23 less ATT's 3 bytes).</summary>
        public const int MinPacket = 20;
        /// <summary>A message longer than this is refused (nothing the session sends comes near it).</summary>
        public const int MaxMessage = 2048;
        public const int LastFlag = 0x80, FirstFlag = 0x40, NumberMask = 0x3F;

        /// <summary>
        /// The packets of one message, each at most <paramref name="maxPacket"/> bytes (header included).
        /// <paramref name="number"/> is the sender's running message count for this peer.
        /// </summary>
        public static List<byte[]> Split(byte[] message, int length, int maxPacket, int number)
        {
            var packets = new List<byte[]>();
            if (message == null || length <= 0 || length > MaxMessage) return packets;
            int chunk = Math.Max(MinPacket, maxPacket) - HeaderBytes;
            int tag = number & NumberMask;
            for (int offset = 0; offset < length; offset += chunk)
            {
                int n = Math.Min(chunk, length - offset);
                var packet = new byte[n + HeaderBytes];
                bool last = offset + n >= length;
                packet[0] = (byte)(tag | (last ? LastFlag : 0) | (offset == 0 ? FirstFlag : 0));
                Array.Copy(message, offset, packet, HeaderBytes, n);
                packets.Add(packet);
            }
            return packets;
        }
    }

    /// <summary>Puts one peer's packets back together into messages (see <see cref="CoopFraming"/>).</summary>
    public sealed class Reassembler
    {
        readonly byte[] buffer = new byte[CoopFraming.MaxMessage];
        int length;
        int number = -1;

        /// <summary>Forget a half-assembled message (the connection dropped).</summary>
        public void Reset()
        {
            length = 0;
            number = -1;
        }

        /// <summary>
        /// Takes one packet. Returns a whole message when this packet was its last, else null.
        /// </summary>
        public byte[] Add(byte[] packet, int count)
        {
            if (packet == null || count < CoopFraming.HeaderBytes) return null;
            int tag = packet[0] & CoopFraming.NumberMask;
            bool last = (packet[0] & CoopFraming.LastFlag) != 0;
            bool first = (packet[0] & CoopFraming.FirstFlag) != 0;
            if (first)
            {
                // A message starts (whatever was being put together is dropped: its end never came).
                length = 0;
                number = tag;
            }
            else if (number != tag)
            {
                // A piece of a message whose start never came (dropped, or cut by a reconnection): throw it away.
                Reset();
                return null;
            }
            int n = count - CoopFraming.HeaderBytes;
            if (length + n > buffer.Length)
            {
                Reset();
                return null;
            }
            Array.Copy(packet, CoopFraming.HeaderBytes, buffer, length, n);
            length += n;
            if (!last) return null;
            var message = new byte[length];
            Array.Copy(buffer, message, length);
            Reset();
            return message;
        }
    }
}
