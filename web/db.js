const DB_NAME = "kai_tank_db";
const STORE = "results";
const VERSION = 1;

let memoryFallback = [];

function openDb() {
  return new Promise((resolve, reject) => {
    if (!("indexedDB" in window)) {
      resolve(null);
      return;
    }
    const req = indexedDB.open(DB_NAME, VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "id", autoIncrement: true });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function saveResult(row) {
  const db = await openDb();
  if (!db) {
    memoryFallback.push({ ...row, id: Date.now() + Math.random() });
    return;
  }
  await new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).add(row);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
}

function sortRows(rows) {
  return rows.sort((a, b) => {
    if (b.rating !== a.rating) return b.rating - a.rating;
    if (b.kills !== a.kills) return b.kills - a.kills;
    return a.playTimeSec - b.playTimeSec;
  });
}

export async function topResults(limit, difficulty) {
  const db = await openDb();
  let rows;
  if (!db) {
    rows = [...memoryFallback];
  } else {
    rows = await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readonly");
      const req = tx.objectStore(STORE).getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
    db.close();
  }
  const filtered = rows.filter((r) => r.difficulty === difficulty);
  return sortRows(filtered).slice(0, limit);
}

export async function bestRating(difficulty) {
  const rows = await topResults(500, difficulty);
  return rows.reduce((acc, row) => Math.max(acc, row.rating), 0);
}
