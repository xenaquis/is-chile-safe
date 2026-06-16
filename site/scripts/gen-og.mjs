/**
 * gen-og.mjs — Offline zero-dependency branded placeholder OG image generator.
 *
 * Writes 7 valid 1200×630 PNGs under site/public/og/ — one per page type.
 * Uses ONLY Node.js builtins: node:zlib, node:fs, node:path.
 * No sharp, no canvas, no npm dependencies.
 *
 * Usage:
 *   node scripts/gen-og.mjs
 *
 * Regenerate any time via:
 *   npm run gen-og
 */

import { deflateSync, crc32 } from 'node:zlib';
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SITE_ROOT = path.resolve(__dirname, '..');
const OUT_DIR = path.join(SITE_ROOT, 'public', 'og');

// ---------------------------------------------------------------------------
// Brand colors per page type (teal #0f766e family, slight tints per type)
// ---------------------------------------------------------------------------
const COLORS = {
  default:   [0x0f, 0x76, 0x6e], // base teal
  home:      [0x0d, 0x94, 0x88], // lighter teal
  commune:   [0x0f, 0x76, 0x6e], // same as default
  region:    [0x13, 0x5e, 0x59], // darker teal
  crime:     [0x1e, 0x40, 0x5e], // teal-blue
  ranking:   [0x17, 0x5e, 0x75], // cyan-teal
  editorial: [0x1e, 0x3a, 0x5f], // deep blue-teal
};

const TYPES = ['default', 'home', 'commune', 'region', 'crime', 'ranking', 'editorial'];

const WIDTH = 1200;
const HEIGHT = 630;

// ---------------------------------------------------------------------------
// CRC32 table (ISO 3309 polynomial, same as PNG spec)
// ---------------------------------------------------------------------------
const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let k = 0; k < 8; k++) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[i] = c;
  }
  return table;
})();

function crc32Buf(buf) {
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i++) {
    crc = CRC_TABLE[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

// ---------------------------------------------------------------------------
// PNG chunk builder
// ---------------------------------------------------------------------------
function makeChunk(type, data) {
  const typeBytes = Buffer.from(type, 'ascii');
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const crcBuf = Buffer.concat([typeBytes, data]);
  const crcVal = Buffer.alloc(4);
  crcVal.writeUInt32BE(crc32Buf(crcBuf), 0);
  return Buffer.concat([len, typeBytes, data, crcVal]);
}

// ---------------------------------------------------------------------------
// IHDR chunk: 1200×630, 8-bit RGB (color type 2), deflate, no interlace
// ---------------------------------------------------------------------------
function makeIHDR(width, height) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;   // bit depth
  ihdr[9] = 2;   // color type: RGB
  ihdr[10] = 0;  // compression: deflate
  ihdr[11] = 0;  // filter: adaptive
  ihdr[12] = 0;  // interlace: none
  return makeChunk('IHDR', ihdr);
}

// ---------------------------------------------------------------------------
// IDAT chunk: solid color scanlines, filter byte 0 per row
// ---------------------------------------------------------------------------
function makeIDAT(width, height, rgb) {
  // Each row: 1 filter byte + width*3 color bytes
  const rowLen = 1 + width * 3;
  const raw = Buffer.alloc(height * rowLen);
  for (let y = 0; y < height; y++) {
    const base = y * rowLen;
    raw[base] = 0; // filter type: None
    for (let x = 0; x < width; x++) {
      const off = base + 1 + x * 3;
      raw[off]     = rgb[0];
      raw[off + 1] = rgb[1];
      raw[off + 2] = rgb[2];
    }
  }
  const compressed = deflateSync(raw, { level: 6 });
  return makeChunk('IDAT', compressed);
}

// ---------------------------------------------------------------------------
// Full PNG: signature + IHDR + IDAT + IEND
// ---------------------------------------------------------------------------
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const IEND = makeChunk('IEND', Buffer.alloc(0));

function buildPng(width, height, rgb) {
  return Buffer.concat([
    PNG_SIGNATURE,
    makeIHDR(width, height),
    makeIDAT(width, height, rgb),
    IEND,
  ]);
}

// ---------------------------------------------------------------------------
// Main: generate + write all 7 PNGs
// ---------------------------------------------------------------------------
mkdirSync(OUT_DIR, { recursive: true });

for (const type of TYPES) {
  const rgb = COLORS[type];
  const png = buildPng(WIDTH, HEIGHT, rgb);
  const outPath = path.join(OUT_DIR, `${type}.png`);
  writeFileSync(outPath, png);
  console.log(`wrote ${outPath} (${png.length} bytes)`);
}

console.log(`\ngen-og: ${TYPES.length} PNGs written to ${OUT_DIR}`);
