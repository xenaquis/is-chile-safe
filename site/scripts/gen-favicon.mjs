/**
 * gen-favicon.mjs — one-off script to generate favicon assets from favicon.svg.
 * Uses the already-installed `sharp` package (no new npm deps).
 * Produces:
 *   - public/apple-touch-icon.png  (180×180, opaque #f5f8f8 background)
 *   - public/favicon.ico           (32×32 PNG wrapped in minimal ICO container)
 *
 * Run: node scripts/gen-favicon.mjs
 */
import { createRequire } from 'module';
import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const sharp = require('sharp');

const svgPath = resolve(__dirname, '../public/favicon.svg');
const svgBuffer = readFileSync(svgPath);

// 1. Generate apple-touch-icon.png (180×180, opaque bg)
const appleBuffer = await sharp(svgBuffer, { density: 300 })
  .resize(180, 180)
  .flatten({ background: { r: 245, g: 248, b: 248 } })
  .png()
  .toBuffer();

writeFileSync(resolve(__dirname, '../public/apple-touch-icon.png'), appleBuffer);
console.log('apple-touch-icon.png generated (180x180)');

// 2. Generate 32×32 PNG for favicon.ico
const ico32Buffer = await sharp(svgBuffer, { density: 300 })
  .resize(32, 32)
  .flatten({ background: { r: 245, g: 248, b: 248 } })
  .png()
  .toBuffer();

// Wrap 32×32 PNG in minimal ICO container (PNG-based ICO):
//   ICONDIR:      6 bytes  (idReserved=0, idType=1, idCount=1)
//   ICONDIRENTRY: 16 bytes (bWidth=32, bHeight=32, bColorCount=0, bReserved=0,
//                           wPlanes=1, wBitCount=32, dwBytesInRes=pngLen,
//                           dwImageOffset=22)
//   PNG data:     N bytes
const pngLen = ico32Buffer.length;
const icoHeader = Buffer.alloc(6 + 16);

// ICONDIR
icoHeader.writeUInt16LE(0, 0);   // idReserved
icoHeader.writeUInt16LE(1, 2);   // idType = 1 (ICO)
icoHeader.writeUInt16LE(1, 4);   // idCount = 1

// ICONDIRENTRY
icoHeader.writeUInt8(32, 6);     // bWidth (32 = 32px; 0 would mean 256)
icoHeader.writeUInt8(32, 7);     // bHeight
icoHeader.writeUInt8(0, 8);      // bColorCount
icoHeader.writeUInt8(0, 9);      // bReserved
icoHeader.writeUInt16LE(1, 10);  // wPlanes
icoHeader.writeUInt16LE(32, 12); // wBitCount
icoHeader.writeUInt32LE(pngLen, 14); // dwBytesInRes
icoHeader.writeUInt32LE(22, 18); // dwImageOffset (6 + 16)

const icoBuffer = Buffer.concat([icoHeader, ico32Buffer]);
writeFileSync(resolve(__dirname, '../public/favicon.ico'), icoBuffer);
console.log('favicon.ico generated (32x32 PNG-in-ICO)');
console.log('First 4 bytes:', icoBuffer.slice(0, 4));
