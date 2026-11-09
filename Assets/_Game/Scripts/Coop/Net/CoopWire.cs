using System;
using System.Text;

namespace DribbleToSchool.Coop.Net
{
    /// <summary>
    /// Writes a co-op message into a byte buffer, little-endian. Strings are UTF-8 with a one-byte length and are cut at a
    /// character boundary so a name never arrives as half a letter. Pure C# (no Unity), so the protocol is tested offline.
    /// </summary>
    public sealed class ByteWriter
    {
        byte[] buffer;
        int length;

        public ByteWriter(int capacity = 256)
        {
            buffer = new byte[Math.Max(16, capacity)];
        }

        public int Length { get { return length; } }
        public byte[] Buffer { get { return buffer; } }

        public void Reset() { length = 0; }

        /// <summary>A copy of what has been written, exactly as long as it.</summary>
        public byte[] ToArray()
        {
            var copy = new byte[length];
            Array.Copy(buffer, copy, length);
            return copy;
        }

        void Ensure(int more)
        {
            if (length + more <= buffer.Length) return;
            var bigger = new byte[Math.Max(buffer.Length * 2, length + more)];
            Array.Copy(buffer, bigger, length);
            buffer = bigger;
        }

        public void U8(int v)
        {
            Ensure(1);
            buffer[length++] = (byte)v;
        }

        public void Bool(bool v) { U8(v ? 1 : 0); }

        public void U16(int v)
        {
            Ensure(2);
            buffer[length++] = (byte)v;
            buffer[length++] = (byte)(v >> 8);
        }

        public void I16(int v)
        {
            if (v > short.MaxValue) v = short.MaxValue;
            if (v < short.MinValue) v = short.MinValue;
            U16((ushort)(short)v);
        }

        public void U32(uint v)
        {
            Ensure(4);
            buffer[length++] = (byte)v;
            buffer[length++] = (byte)(v >> 8);
            buffer[length++] = (byte)(v >> 16);
            buffer[length++] = (byte)(v >> 24);
        }

        public void I32(int v) { U32((uint)v); }

        public void F32(float v)
        {
            var bytes = BitConverter.GetBytes(v);
            if (!BitConverter.IsLittleEndian) Array.Reverse(bytes);
            Ensure(4);
            for (int i = 0; i < 4; i++) buffer[length++] = bytes[i];
        }

        /// <summary>UTF-8, at most <paramref name="maxBytes"/> bytes (cut between characters), one length byte first.</summary>
        public void Str(string s, int maxBytes = 48)
        {
            byte[] bytes = Utf8Truncate(s ?? "", Math.Min(255, maxBytes));
            U8(bytes.Length);
            Raw(bytes, 0, bytes.Length);
        }

        public void Raw(byte[] data, int offset, int count)
        {
            Ensure(count);
            Array.Copy(data, offset, buffer, length, count);
            length += count;
        }

        /// <summary>The UTF-8 bytes of <paramref name="s"/>, cut to at most <paramref name="maxBytes"/> without splitting a character.</summary>
        public static byte[] Utf8Truncate(string s, int maxBytes)
        {
            var bytes = Encoding.UTF8.GetBytes(s ?? "");
            if (bytes.Length <= maxBytes) return bytes;
            int cut = maxBytes;
            // Step back over continuation bytes (10xxxxxx) so the cut falls at the start of a character.
            while (cut > 0 && (bytes[cut] & 0xC0) == 0x80) cut--;
            var result = new byte[cut];
            Array.Copy(bytes, result, cut);
            return result;
        }
    }

    /// <summary>Reads what a <see cref="ByteWriter"/> wrote. Reading past the end sets <see cref="Failed"/> and returns zeros, never throws.</summary>
    public sealed class ByteReader
    {
        readonly byte[] data;
        readonly int end;
        int pos;

        public ByteReader(byte[] data, int offset, int count)
        {
            this.data = data ?? new byte[0];
            pos = Math.Max(0, offset);
            end = Math.Min(this.data.Length, pos + Math.Max(0, count));
        }

        public ByteReader(byte[] data) : this(data, 0, data != null ? data.Length : 0) { }

        /// <summary>True once a read ran past the end of the message: what was read is not to be trusted.</summary>
        public bool Failed { get; private set; }
        public int Remaining { get { return end - pos; } }

        bool Have(int n)
        {
            if (pos + n <= end) return true;
            Failed = true;
            pos = end;
            return false;
        }

        public int U8()
        {
            if (!Have(1)) return 0;
            return data[pos++];
        }

        public bool Bool() { return U8() != 0; }

        public int U16()
        {
            if (!Have(2)) return 0;
            int v = data[pos] | (data[pos + 1] << 8);
            pos += 2;
            return v;
        }

        public int I16() { return (short)(ushort)U16(); }

        public uint U32()
        {
            if (!Have(4)) return 0;
            uint v = (uint)(data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16) | (data[pos + 3] << 24));
            pos += 4;
            return v;
        }

        public int I32() { return (int)U32(); }

        public float F32()
        {
            if (!Have(4)) return 0f;
            var bytes = new byte[4];
            Array.Copy(data, pos, bytes, 0, 4);
            pos += 4;
            if (!BitConverter.IsLittleEndian) Array.Reverse(bytes);
            float f = BitConverter.ToSingle(bytes, 0);
            return float.IsNaN(f) || float.IsInfinity(f) ? 0f : f;
        }

        public string Str()
        {
            int n = U8();
            if (!Have(n)) return "";
            string s;
            try { s = Encoding.UTF8.GetString(data, pos, n); }
            catch (Exception) { s = ""; }
            pos += n;
            return s;
        }

        public byte[] Raw(int n)
        {
            if (!Have(n)) return new byte[0];
            var copy = new byte[n];
            Array.Copy(data, pos, copy, 0, n);
            pos += n;
            return copy;
        }
    }
}
