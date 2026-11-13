/**
 * Pocket Cube (2x2 Rubik's Cube) JavaScript Model
 * Exact match to backend Python implementation & PDF specification.
 */

// Corner slot definitions:
// 0: UFL, 1: UFR, 2: UBR, 3: UBL, 4: DFL, 5: DFR, 6: DBR, 7: DBL (fixed reference corner)
export const CORNER_NAMES = ["UFL", "UFR", "UBR", "UBL", "DFL", "DFR", "DBR", "DBL"];

// Standard 6 quarter-turns for the assignment's state-space search (DBL fixed)
export const MOVE_NAMES = ["U", "U'", "R", "R'", "F", "F'"];

// Complete 12 face turns supported for physical cube exploration
export const ALL_MOVE_NAMES = ["U", "U'", "R", "R'", "F", "F'", "D", "D'", "L", "L'", "B", "B'"];

export const INVERSE_MOVE = {
  "U": "U'", "U'": "U",
  "R": "R'", "R'": "R",
  "F": "F'", "F'": "F",
  "D": "D'", "D'": "D",
  "L": "L'", "L'": "L",
  "B": "B'", "B'": "B",
};

export const MOVE_EXPLANATIONS = {
  "R":  { face: "Right", direction: "Clockwise", text: "Rotate Right face clockwise 90°" },
  "R'": { face: "Right", direction: "Counterclockwise", text: "Rotate Right face counterclockwise 90°" },
  "U":  { face: "Upper", direction: "Clockwise", text: "Rotate Upper face clockwise 90°" },
  "U'": { face: "Upper", direction: "Counterclockwise", text: "Rotate Upper face counterclockwise 90°" },
  "F":  { face: "Front", direction: "Clockwise", text: "Rotate Front face clockwise 90°" },
  "F'": { face: "Front", direction: "Counterclockwise", text: "Rotate Front face counterclockwise 90°" },
  "D":  { face: "Down", direction: "Clockwise", text: "Rotate Down face clockwise 90°" },
  "D'": { face: "Down", direction: "Counterclockwise", text: "Rotate Down face counterclockwise 90°" },
  "L":  { face: "Left", direction: "Clockwise", text: "Rotate Left face clockwise 90°" },
  "L'": { face: "Left", direction: "Counterclockwise", text: "Rotate Left face counterclockwise 90°" },
  "B":  { face: "Back", direction: "Clockwise", text: "Rotate Back face clockwise 90°" },
  "B'": { face: "Back", direction: "Counterclockwise", text: "Rotate Back face counterclockwise 90°" },
};

// Colors
export const COLOR_WHITE  = 0;
export const COLOR_YELLOW = 1;
export const COLOR_GREEN  = 2;
export const COLOR_BLUE   = 3;
export const COLOR_RED    = 4;
export const COLOR_ORANGE = 5;

export const COLOR_HEX = {
  0: "#ffffff", // White (U)
  1: "#ffd700", // Yellow (D)
  2: "#00c853", // Green (F)
  3: "#1565c0", // Blue (B)
  4: "#ef4444", // Red (R)
  5: "#ff6d00", // Orange (L)
};

export const FACE_NAMES = ["U", "D", "F", "B", "R", "L"];

// Move tables (8 corners, index 7 is DBL)
const U_PERM   = [1, 2, 3, 0, 4, 5, 6, 7];
const U_ORIENT = [0, 0, 0, 0, 0, 0, 0, 0];

const Ui_PERM   = [3, 0, 1, 2, 4, 5, 6, 7];
const Ui_ORIENT = [0, 0, 0, 0, 0, 0, 0, 0];

const R_PERM   = [0, 5, 1, 3, 4, 6, 2, 7];
const R_ORIENT = [0, 1, 2, 0, 0, 2, 1, 0];

const Ri_PERM   = [0, 2, 6, 3, 4, 1, 5, 7];
const Ri_ORIENT = [0, 1, 2, 0, 0, 2, 1, 0];

const F_PERM   = [4, 0, 2, 3, 5, 1, 6, 7];
const F_ORIENT = [1, 2, 0, 0, 2, 1, 0, 0];

const Fi_PERM   = [1, 5, 2, 3, 0, 4, 6, 7];
const Fi_ORIENT = [1, 2, 0, 0, 2, 1, 0, 0];

const D_PERM   = [0, 1, 2, 3, 7, 4, 5, 6];
const D_ORIENT = [0, 0, 0, 0, 0, 0, 0, 0];

const Di_PERM   = [0, 1, 2, 3, 5, 6, 7, 4];
const Di_ORIENT = [0, 0, 0, 0, 0, 0, 0, 0];

const L_PERM   = [3, 1, 2, 7, 0, 5, 6, 4];
const L_ORIENT = [2, 0, 0, 1, 1, 0, 0, 2];

const Li_PERM   = [4, 1, 2, 0, 7, 5, 6, 3];
const Li_ORIENT = [2, 0, 0, 1, 1, 0, 0, 2];

const B_PERM   = [0, 1, 6, 2, 4, 5, 7, 3];
const B_ORIENT = [0, 0, 1, 2, 0, 0, 2, 1];

const Bi_PERM   = [0, 1, 3, 7, 4, 5, 2, 6];
const Bi_ORIENT = [0, 0, 1, 2, 0, 0, 2, 1];

const MOVES = {
  "U":  [U_PERM,  U_ORIENT],
  "U'": [Ui_PERM, Ui_ORIENT],
  "R":  [R_PERM,  R_ORIENT],
  "R'": [Ri_PERM, Ri_ORIENT],
  "F":  [F_PERM,  F_ORIENT],
  "F'": [Fi_PERM, Fi_ORIENT],
  "D":  [D_PERM,  D_ORIENT],
  "D'": [Di_PERM, Di_ORIENT],
  "L":  [L_PERM,  L_ORIENT],
  "L'": [Li_PERM, Li_ORIENT],
  "B":  [B_PERM,  B_ORIENT],
  "B'": [Bi_PERM, Bi_ORIENT],
};

export function getSolvedState() {
  return {
    perm: [0, 1, 2, 3, 4, 5, 6],
    orient: [0, 0, 0, 0, 0, 0, 0]
  };
}

export function isSolved(state) {
  for (let i = 0; i < 7; i++) {
    if (state.perm[i] !== i || state.orient[i] !== 0) return false;
  }
  return true;
}

function applyRaw8(p, o, m) {
  const [pe, oe] = MOVES[m];
  const np = new Array(8);
  const no = new Array(8);
  for (let i = 0; i < 8; i++) {
    np[i] = p[pe[i]];
    no[i] = (o[pe[i]] + oe[i]) % 3;
  }
  return [np, no];
}

const rotX = (p, o) => { const [p1, o1] = applyRaw8(p, o, "R"); return applyRaw8(p1, o1, "L'"); };
const rotY = (p, o) => { const [p1, o1] = applyRaw8(p, o, "U"); return applyRaw8(p1, o1, "D'"); };
const rotZ = (p, o) => { const [p1, o1] = applyRaw8(p, o, "F"); return applyRaw8(p1, o1, "B'"); };

const ROTATIONS = (() => {
  const solvedP = [0,1,2,3,4,5,6,7];
  const solvedO = [0,0,0,0,0,0,0,0];
  const key = (p, o) => p.join(',') + '|' + o.join(',');
  const visited = new Map();
  visited.set(key(solvedP, solvedO), []);
  const q = [[solvedP, solvedO]];
  const gens = [rotX, rotY, rotZ];

  while (q.length > 0) {
    const [cp, co] = q.shift();
    const path = visited.get(key(cp, co));
    for (const fn of gens) {
      const [np, no] = fn(cp, co);
      const k = key(np, no);
      if (!visited.has(k)) {
        visited.set(k, [...path, fn]);
        q.push([np, no]);
      }
    }
  }
  return Array.from(visited.values());
})();

export function normalizeState8(p, o) {
  if (p[7] === 7 && o[7] === 0) return [p, o];
  for (const path of ROTATIONS) {
    let cp = p;
    let co = o;
    for (const fn of path) {
      [cp, co] = fn(cp, co);
    }
    if (cp[7] === 7 && co[7] === 0) {
      return [cp, co];
    }
  }
  return [p, o];
}

export function applyMove(state, moveName) {
  const fullPerm = state.perm.length === 7 ? [...state.perm, 7] : [...state.perm];
  const fullOrient = state.orient.length === 7 ? [...state.orient, 0] : [...state.orient];

  let [newPerm, newOrient] = applyRaw8(fullPerm, fullOrient, moveName);
  if (newPerm[7] !== 7 || newOrient[7] !== 0) {
    [newPerm, newOrient] = normalizeState8(newPerm, newOrient);
  }

  return {
    perm: newPerm.slice(0, 7),
    orient: newOrient.slice(0, 7)
  };
}

export function applyMoves(state, moveSequence) {
  let s = state;
  for (const m of moveSequence) {
    s = applyMove(s, m);
  }
  return s;
}

export function invertSequence(moveSequence) {
  return [...moveSequence].reverse().map(m => INVERSE_MOVE[m] || m);
}

export function sameFace(m1, m2) {
  return m1.replace("'", "") === m2.replace("'", "");
}

// Corner stickers map in canonical order [U/D sticker, CW next sticker, CCW next sticker]
const CORNER_COLORS = [
  [COLOR_WHITE,  COLOR_ORANGE, COLOR_GREEN], // 0: UFL
  [COLOR_WHITE,  COLOR_GREEN,  COLOR_RED],   // 1: UFR
  [COLOR_WHITE,  COLOR_RED,    COLOR_BLUE],  // 2: UBR
  [COLOR_WHITE,  COLOR_BLUE,   COLOR_ORANGE],// 3: UBL
  [COLOR_YELLOW, COLOR_GREEN,  COLOR_ORANGE],// 4: DFL
  [COLOR_YELLOW, COLOR_RED,    COLOR_GREEN], // 5: DFR
  [COLOR_YELLOW, COLOR_BLUE,   COLOR_RED],   // 6: DBR
  [COLOR_YELLOW, COLOR_ORANGE, COLOR_BLUE],  // 7: DBL (fixed)
];

export function stateToStickers(state) {
  const fullPerm = state.perm.length === 7 ? [...state.perm, 7] : [...state.perm];
  const fullOrient = state.orient.length === 7 ? [...state.orient, 0] : [...state.orient];

  const slotStickers = [];
  for (let slot = 0; slot < 8; slot++) {
    const piece = fullPerm[slot];
    const twist = fullOrient[slot];
    const colors = CORNER_COLORS[piece];
    slotStickers.push([
      colors[(0 + 3 - twist) % 3],
      colors[(1 + 3 - twist) % 3],
      colors[(2 + 3 - twist) % 3],
    ]);
  }

  return {
    U: [slotStickers[3][0], slotStickers[2][0], slotStickers[0][0], slotStickers[1][0]],
    D: [slotStickers[4][0], slotStickers[5][0], slotStickers[7][0], slotStickers[6][0]],
    F: [slotStickers[0][2], slotStickers[1][1], slotStickers[4][1], slotStickers[5][2]],
    B: [slotStickers[2][2], slotStickers[3][1], slotStickers[6][1], slotStickers[7][2]],
    R: [slotStickers[1][2], slotStickers[2][1], slotStickers[5][1], slotStickers[6][2]],
    L: [slotStickers[3][2], slotStickers[0][1], slotStickers[7][1], slotStickers[4][2]],
  };
}
