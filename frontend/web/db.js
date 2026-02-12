const DB_NAME = "kai_tank_db";
const STORE = "results";
const VERSION = 1;
const API_BASE_URL = window.localStorage.getItem("api_base_url") || "http://localhost:8081";

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

async function saveLocalResult(row) {
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

async function topLocalResults(limit, difficulty) {
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

function toApiPayload(row) {
  return {
    playerName: row.playerName,
    difficulty: row.difficulty,
    rating: Number(row.rating),
    kills: Number(row.kills),
    deaths: Number(row.deaths || 0),
    bulletsUsed: Number(row.bulletsUsed || 0),
    levelReached: Number(row.levelReached || 1),
    victory: Number(row.victory || 0),
    playTimeSec: Number(row.playTimeSec || 0),
    timeMs: Math.max(0, Math.round(Number(row.playTimeSec || 0) * 1000)),
    playedAt: row.playedAt || new Date().toISOString(),
  };
}

function fromApiRow(row) {
  return {
    id: row.id,
    playerName: row.playerName,
    difficulty: row.difficulty,
    rating: Number(row.rating || 0),
    kills: Number(row.kills || 0),
    deaths: Number(row.deaths || 0),
    bulletsUsed: Number(row.bulletsUsed || 0),
    levelReached: Number(row.levelReached || 1),
    victory: Number(row.victory || 0),
    playTimeSec: Number(row.playTimeSec || 0),
    playedAt: row.playedAt || new Date(Number(row.createdAt || Date.now())).toISOString(),
  };
}

async function saveRemoteResult(row) {
  const res = await fetch(`${API_BASE_URL}/api/scores`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(toApiPayload(row)),
  });
  if (!res.ok) {
    throw new Error(`save score failed: ${res.status}`);
  }
  return res.json();
}

async function topRemoteResults(limit, difficulty) {
  const params = new URLSearchParams({
    limit: String(limit),
    difficulty,
  });
  const res = await fetch(`${API_BASE_URL}/api/scores/leaderboard?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`load leaderboard failed: ${res.status}`);
  }
  const rows = await res.json();
  return (Array.isArray(rows) ? rows : []).map(fromApiRow);
}

export async function saveResult(row) {
  try {
    await saveRemoteResult(row);
    return;
  } catch (_) {
    await saveLocalResult(row);
  }
}

export async function topResults(limit, difficulty) {
  try {
    return await topRemoteResults(limit, difficulty);
  } catch (_) {
    return topLocalResults(limit, difficulty);
  }
}

export async function bestRating(difficulty) {
  const rows = await topResults(500, difficulty);
  return rows.reduce((acc, row) => Math.max(acc, row.rating), 0);
}
