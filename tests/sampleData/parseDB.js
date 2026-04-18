const { open } = require("fs/promises");

// Helper to convert little endian byte array to BigInt
function littleEndianToBigInt(byteArray) {
  let bigEndianBytes = Buffer.alloc(byteArray.length);
  for (let i = 0; i < byteArray.length; i++) {
    bigEndianBytes[i] = byteArray[byteArray.length - i - 1];
  }
  return BigInt("0x" + bigEndianBytes.toString("hex"));
}

// Helper to read a specific number of bytes at a given offset
async function readBytesAtPosition(handler, buffer, position, length) {
  const { bytesRead } = await handler.read(buffer, 0, length, position);
  return bytesRead;
}

// Parses the mhod (metadata) blocks for a track
async function parsemhod(track, handler, startOffset, headerSize) {
  let bytesOffset = startOffset + headerSize - 4;
  const dword = Buffer.alloc(4);
  bytesOffset += 8;

  const totalSize = await readBytesAtPosition(handler, dword, bytesOffset, 4);
  const totalSizeValue = Number(littleEndianToBigInt(dword));
  bytesOffset += 4;

  const mhodType = await readBytesAtPosition(handler, dword, bytesOffset, 4);
  const mhodTypeValue = Number(littleEndianToBigInt(dword));
  bytesOffset += 4;

  if (mhodTypeValue === 1 || mhodTypeValue === 3 || mhodTypeValue === 4) {
    bytesOffset += 12;

    const stringLength = await readBytesAtPosition(
      handler,
      dword,
      bytesOffset,
      4,
    );
    const stringLengthValue = Number(littleEndianToBigInt(dword));
    bytesOffset += 12;

    const dataArray = Buffer.alloc(stringLengthValue);
    await readBytesAtPosition(
      handler,
      dataArray,
      bytesOffset,
      stringLengthValue,
    );
    const stringData = dataArray.toString("utf16le");

    switch (mhodTypeValue) {
      case 1:
        track.track = stringData;
        break; // Title
      case 3:
        track.album = stringData;
        break; // Album
      case 4:
        track.artist = stringData;
        break; // Artist
    }
  }
  return totalSizeValue;
}

// Parses the mhit (track item) block
async function parseMhit(handler, startOffset) {
  const track = {};
  let bytesOffset = startOffset;
  let totalSize = 0;
  const dword = Buffer.alloc(4);

  await readBytesAtPosition(handler, dword, bytesOffset, 4);
  const headerSize = Number(littleEndianToBigInt(dword));
  bytesOffset += 4;

  bytesOffset += 4; // Skip 4 bytes

  await readBytesAtPosition(handler, dword, bytesOffset, 4);
  const mhodEntriesCount = Number(littleEndianToBigInt(dword));
  bytesOffset += 4;

  await readBytesAtPosition(handler, dword, bytesOffset, 4);
  track.id = Number(littleEndianToBigInt(dword));
  bytesOffset += 4;

  bytesOffset += 20; // Skip 20 bytes

  await readBytesAtPosition(handler, dword, bytesOffset, 4);
  track.length = Number(littleEndianToBigInt(dword));
  bytesOffset += 4;

  for (let i = 0; i < mhodEntriesCount; ++i) {
    totalSize = await parsemhod(track, handler, startOffset, headerSize);
    startOffset += totalSize;
  }
  return track;
}

// Main iTunesDB parser
async function parseItunesDb(filePath) {
  let tracklist = [];
  const handler = await open(filePath, "r");
  const bufferSize = 1024 * 1024; // 1 MB chunk
  const buffer = Buffer.alloc(bufferSize);
  let totalBytesRead = 0;

  while (true) {
    const bytesRead = await readBytesAtPosition(
      handler,
      buffer,
      totalBytesRead,
      bufferSize,
    );
    for (let i = 0; i < bytesRead; i++) {
      if (buffer[i] === 109 && bytesRead - i >= 4) {
        // Look for 'm'
        const nextBytes = buffer.toString("utf8", i + 1, i + 4);
        if (nextBytes === "hit") {
          // Look for 'hit' ('mhit' marker)
          const track = await parseMhit(handler, totalBytesRead + i + 4);
          tracklist.push(track);
        }
      }
    }
    totalBytesRead += bytesRead;
    if (bytesRead < bufferSize) break; // EOF
  }
  await handler.close();
  return tracklist;
}

// Parses Play Counts and merges it with the tracklist
async function parsePlayCounts(filePath, tracklist) {
  const handler = await open(filePath, "r");
  let bytesOffset = 8; // Skip 8-byte header
  const dword = Buffer.alloc(4);

  await readBytesAtPosition(handler, dword, bytesOffset, 4);
  const entryLen = Number(littleEndianToBigInt(dword));
  bytesOffset += 4;

  await readBytesAtPosition(handler, dword, bytesOffset, 4);
  const numEntries = Number(littleEndianToBigInt(dword));
  bytesOffset += 4;

  bytesOffset += 80; // Skip 80 bytes padding

  for (let i = 0; i < numEntries - 1; i++) {
    if (i >= tracklist.length) {
      bytesOffset += entryLen; // Bounds check
      continue;
    }

    let savedBytes = bytesOffset;
    await readBytesAtPosition(handler, dword, bytesOffset, 4);
    const playCount = Number(littleEndianToBigInt(dword));
    bytesOffset += 4;

    if (playCount > 0) {
      await readBytesAtPosition(handler, dword, bytesOffset, 4);
      let lastPlayed = Number(littleEndianToBigInt(dword));
      bytesOffset += 4;

      // Convert Mac HFS time to Unix time
      lastPlayed -= 2082844800;

      // Apply local timezone offset
      const offset = new Date().getTimezoneOffset() * 60;
      lastPlayed += offset;

      tracklist[i].playCount = playCount;
      tracklist[i].lastPlayed = lastPlayed;
    }

    // Jump to the next entry
    bytesOffset = savedBytes + entryLen;
  }
  await handler.close();
}

async function main() {
  try {
    console.log("Parsing iTunesDB...");
    const tracklist = await parseItunesDb("./iTunesDB");
    console.log(`Found ${tracklist.length} tracks in iTunesDB.\n`);

    console.log("Parsing Play Counts...");
    await parsePlayCounts("./Play Counts", tracklist);

    // Filter down to only tracks that have plays
    const playedTracks = tracklist.filter(
      (t) => t.playCount && t.playCount > 0,
    );

    // Sort descending by last played time
    playedTracks.sort((a, b) => b.lastPlayed - a.lastPlayed);

    console.log(`\nFound ${playedTracks.length} tracks with play counts:\n`);

    console.log(playedTracks[0]); // Log the most recently played track for debugging

    playedTracks.forEach((track) => {
      // Multiply by 1000 since JS Date expects milliseconds
      const date = new Date(track.lastPlayed * 1000).toLocaleString();
      const artist = track.artist || "Unknown Artist";
      const title = track.track || "Unknown Title";
      console.log(`[${date}] ${artist} - ${title} (Plays: ${track.playCount})`);
    });
  } catch (err) {
    console.error(
      'Error parsing files. Ensure "iTunesDB" and "Play Counts" are in the current directory.',
      err.message,
    );
  }
}

main().catch((err) => {
  console.error("Fatal error", err);
  process.exit(1);
});
