/**
 * Interactive 3D Pocket Cube (2x2 Rubik's Cube) Visualization Engine
 * Powered by Three.js & OrbitControls
 *
 * Implements:
 * - 8 individual physical corner cubies with realistic plastic materials & colored stickers.
 * - OrbitControls for free mouse camera rotation (click+drag) and zoom (scroll).
 * - Physical 3D face-turn animations (groups 4 cubies and rotates them 90 degrees around face axis).
 * - Synchronization with mathematical (perm, orient) state tuples.
 */

import * as THREE from './vendor/three.module.js';
import { OrbitControls } from './vendor/OrbitControls.js';

// Rubik's Cube standard sticker colors
export const COLORS = {
  U: 0xffffff, // White
  D: 0xffd700, // Yellow
  F: 0x00c853, // Green
  B: 0x1565c0, // Blue
  R: 0xef4444, // Red
  L: 0xff6d00, // Orange
  CORE: 0x111317, // Dark black plastic core
};

// Slot index to initial 3D position [x, y, z]
// 0: UFL (-0.5, +0.5, +0.5)
// 1: UFR (+0.5, +0.5, +0.5)
// 2: UBR (+0.5, +0.5, -0.5)
// 3: UBL (-0.5, +0.5, -0.5)
// 4: DFL (-0.5, -0.5, +0.5)
// 5: DFR (+0.5, -0.5, +0.5)
// 6: DBR (+0.5, -0.5, -0.5)
// 7: DBL (-0.5, -0.5, -0.5) [fixed reference corner]
export const SLOT_POSITIONS = [
  [-0.5,  0.5,  0.5], // 0: UFL
  [ 0.5,  0.5,  0.5], // 1: UFR
  [ 0.5,  0.5, -0.5], // 2: UBR
  [-0.5,  0.5, -0.5], // 3: UBL
  [-0.5, -0.5,  0.5], // 4: DFL
  [ 0.5, -0.5,  0.5], // 5: DFR
  [ 0.5, -0.5, -0.5], // 6: DBR
  [-0.5, -0.5, -0.5], // 7: DBL
];

// Face turn configurations
// Axis of rotation and direction for CLOCKWISE turns (looking directly at face):
// - U: +Y axis, looking down at +Y -> clockwise rotates around +Y with angle -PI/2
// - D: +Y axis, looking up at -Y   -> clockwise rotates around +Y with angle +PI/2
// - R: +X axis, looking from +X    -> clockwise rotates around +X with angle -PI/2
// - L: +X axis, looking from -X    -> clockwise rotates around +X with angle +PI/2
// - F: +Z axis, looking from +Z    -> clockwise rotates around +Z with angle -PI/2
// - B: +Z axis, looking from -Z    -> clockwise rotates around +Z with angle +PI/2
export const FACE_CONFIGS = {
  "U":  { axis: new THREE.Vector3(0, 1, 0), angle: -Math.PI / 2, filter: (p) => p.y > 0.1 },
  "U'": { axis: new THREE.Vector3(0, 1, 0), angle:  Math.PI / 2, filter: (p) => p.y > 0.1 },
  "D":  { axis: new THREE.Vector3(0, 1, 0), angle:  Math.PI / 2, filter: (p) => p.y < -0.1 },
  "D'": { axis: new THREE.Vector3(0, 1, 0), angle: -Math.PI / 2, filter: (p) => p.y < -0.1 },
  "R":  { axis: new THREE.Vector3(1, 0, 0), angle: -Math.PI / 2, filter: (p) => p.x > 0.1 },
  "R'": { axis: new THREE.Vector3(1, 0, 0), angle:  Math.PI / 2, filter: (p) => p.x > 0.1 },
  "L":  { axis: new THREE.Vector3(1, 0, 0), angle:  Math.PI / 2, filter: (p) => p.x < -0.1 },
  "L'": { axis: new THREE.Vector3(1, 0, 0), angle: -Math.PI / 2, filter: (p) => p.x < -0.1 },
  "F":  { axis: new THREE.Vector3(0, 0, 1), angle: -Math.PI / 2, filter: (p) => p.z > 0.1 },
  "F'": { axis: new THREE.Vector3(0, 0, 1), angle:  Math.PI / 2, filter: (p) => p.z > 0.1 },
  "B":  { axis: new THREE.Vector3(0, 0, 1), angle:  Math.PI / 2, filter: (p) => p.z < -0.1 },
  "B'": { axis: new THREE.Vector3(0, 0, 1), angle: -Math.PI / 2, filter: (p) => p.z < -0.1 },
};

export class Cube3D {
  constructor(containerElement) {
    this.container = containerElement;
    this.cubies = []; // 8 cubie Object3Ds
    this.cubeGroup = new THREE.Group();
    this.isAnimating = false;
    this.animationQueue = [];

    this._initScene();
    this._createCubies();
    this._initLighting();
    this._setupResizeHandler();
    this._animate();
  }

  _initScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0b0f19);

    const width = this.container.clientWidth || 500;
    const height = this.container.clientHeight || 450;

    this.camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
    this.defaultCameraPos = new THREE.Vector3(3.2, 2.5, 3.8);
    this.camera.position.copy(this.defaultCameraPos);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    this.container.innerHTML = '';
    this.container.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 2.5;
    this.controls.maxDistance = 8.5;
    this.controls.target.set(0, 0, 0);

    this.scene.add(this.cubeGroup);
  }

  _initLighting() {
    // Ambient light for base illumination
    const ambient = new THREE.AmbientLight(0xffffff, 1.2);
    this.scene.add(ambient);

    // Key directional light with soft shadows
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.8);
    keyLight.position.set(5, 8, 6);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    this.scene.add(keyLight);

    // Fill light from opposite side
    const fillLight = new THREE.DirectionalLight(0x93c5fd, 0.9);
    fillLight.position.set(-6, -4, -5);
    this.scene.add(fillLight);

    // Top rim light
    const topLight = new THREE.DirectionalLight(0xffffff, 0.8);
    topLight.position.set(0, 8, 0);
    this.scene.add(topLight);
  }

  _createCubies() {
    // Each cubie is a black plastic cube with colored sticker plates on exposed faces
    const cubieSize = 0.92;
    const stickerSize = 0.82;
    const stickerThickness = 0.03;
    const gapOffset = 0.52; // distance from origin to cubie center (0.5 + small gap)

    // Plastic material for cubie body
    const plasticMaterial = new THREE.MeshStandardMaterial({
      color: COLORS.CORE,
      roughness: 0.35,
      metalness: 0.1,
    });

    const stickerMaterials = {
      U: new THREE.MeshStandardMaterial({ color: COLORS.U, roughness: 0.15, metalness: 0.05 }),
      D: new THREE.MeshStandardMaterial({ color: COLORS.D, roughness: 0.15, metalness: 0.05 }),
      F: new THREE.MeshStandardMaterial({ color: COLORS.F, roughness: 0.15, metalness: 0.05 }),
      B: new THREE.MeshStandardMaterial({ color: COLORS.B, roughness: 0.15, metalness: 0.05 }),
      R: new THREE.MeshStandardMaterial({ color: COLORS.R, roughness: 0.15, metalness: 0.05 }),
      L: new THREE.MeshStandardMaterial({ color: COLORS.L, roughness: 0.15, metalness: 0.05 }),
    };

    const boxGeom = new THREE.BoxGeometry(cubieSize, cubieSize, cubieSize);
    const stickerGeom = new THREE.BoxGeometry(stickerSize, stickerSize, stickerThickness);

    for (let i = 0; i < 8; i++) {
      const [initX, initY, initZ] = SLOT_POSITIONS[i];
      const posX = initX * gapOffset * 2;
      const posY = initY * gapOffset * 2;
      const posZ = initZ * gapOffset * 2;

      const cubieGroup = new THREE.Group();
      cubieGroup.position.set(posX, posY, posZ);
      cubieGroup.userData = { id: i, originalSlot: i };

      // Base black cubie
      const baseMesh = new THREE.Mesh(boxGeom, plasticMaterial);
      baseMesh.castShadow = true;
      baseMesh.receiveShadow = true;
      cubieGroup.add(baseMesh);

      const halfSize = cubieSize / 2 + stickerThickness / 2;

      // Add stickers only on outer faces:
      // U (+Y)
      if (initY > 0) {
        const s = new THREE.Mesh(stickerGeom, stickerMaterials.U);
        s.position.set(0, halfSize, 0);
        s.rotation.x = -Math.PI / 2;
        cubieGroup.add(s);
      }
      // D (-Y)
      if (initY < 0) {
        const s = new THREE.Mesh(stickerGeom, stickerMaterials.D);
        s.position.set(0, -halfSize, 0);
        s.rotation.x = Math.PI / 2;
        cubieGroup.add(s);
      }
      // F (+Z)
      if (initZ > 0) {
        const s = new THREE.Mesh(stickerGeom, stickerMaterials.F);
        s.position.set(0, 0, halfSize);
        cubieGroup.add(s);
      }
      // B (-Z)
      if (initZ < 0) {
        const s = new THREE.Mesh(stickerGeom, stickerMaterials.B);
        s.position.set(0, 0, -halfSize);
        s.rotation.y = Math.PI;
        cubieGroup.add(s);
      }
      // R (+X)
      if (initX > 0) {
        const s = new THREE.Mesh(stickerGeom, stickerMaterials.R);
        s.position.set(halfSize, 0, 0);
        s.rotation.y = Math.PI / 2;
        cubieGroup.add(s);
      }
      // L (-X)
      if (initX < 0) {
        const s = new THREE.Mesh(stickerGeom, stickerMaterials.L);
        s.position.set(-halfSize, 0, 0);
        s.rotation.y = -Math.PI / 2;
        cubieGroup.add(s);
      }

      this.cubies.push(cubieGroup);
      this.cubeGroup.add(cubieGroup);
    }
  }

  _setupResizeHandler() {
    const handleResize = () => {
      const width = this.container.clientWidth;
      const height = this.container.clientHeight;
      if (width && height) {
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
      }
    };

    window.addEventListener('resize', handleResize);
    if (typeof ResizeObserver !== 'undefined') {
      new ResizeObserver(handleResize).observe(this.container);
    }
    requestAnimationFrame(handleResize);
  }

  _animate = () => {
    requestAnimationFrame(this._animate);
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  };

  /**
   * Reset camera to default perspective.
   */
  resetCamera() {
    this.camera.position.copy(this.defaultCameraPos);
    this.controls.target.set(0, 0, 0);
    this.controls.update();
  }

  /**
   * Physically animate a face turn (e.g. "R", "U'", "F").
   *
   * @param {string} moveName - Notation such as "U", "U'", "R", "R'", "F", "F'", etc.
   * @param {number} durationMs - Duration of the turn in milliseconds.
   * @returns {Promise<void>} Resolves when the 90-degree turn completes.
   */
  animateMove(moveName, durationMs = 350) {
    return new Promise((resolve) => {
      const config = FACE_CONFIGS[moveName];
      if (!config) {
        console.warn(`Unknown move: ${moveName}`);
        resolve();
        return;
      }

      if (this.isAnimating) {
        this.animationQueue.push({ moveName, durationMs, resolve });
        return;
      }

      this.isAnimating = true;

      // 1. Identify the 4 cubies on this face by current world position
      const movingCubies = [];
      const worldPos = new THREE.Vector3();

      for (const cubie of this.cubies) {
        cubie.getWorldPosition(worldPos);
        if (config.filter(worldPos)) {
          movingCubies.push(cubie);
        }
      }

      // 2. Create a temporary pivot group centered at (0,0,0)
      const pivot = new THREE.Group();
      this.scene.add(pivot);

      // Attach the 4 cubies to pivot (preserves world position & orientation)
      for (const cubie of movingCubies) {
        pivot.attach(cubie);
      }

      // 3. Smooth animation using requestAnimationFrame
      const startTime = performance.now();
      const targetAngle = config.angle;
      const rotAxis = config.axis;

      const animateStep = (now) => {
        const elapsed = now - startTime;
        const progress = Math.min(1.0, elapsed / durationMs);

        // Sinusoidal smooth ease-in-out
        const ease = (1 - Math.cos(progress * Math.PI)) / 2;
        const currentAngle = targetAngle * ease;

        // Apply rotation around the face axis
        pivot.rotation.set(0, 0, 0);
        pivot.rotateOnAxis(rotAxis, currentAngle);

        if (progress < 1.0) {
          requestAnimationFrame(animateStep);
        } else {
          // Snap exactly to target angle
          pivot.rotation.set(0, 0, 0);
          pivot.rotateOnAxis(rotAxis, targetAngle);
          pivot.updateMatrixWorld(true);

          // 4. Detach cubies back to cubeGroup with committed rotation
          const gapOffset = 0.52;
          for (const cubie of movingCubies) {
            this.cubeGroup.attach(cubie);
            // Snap position to canonical slot coordinates to prevent floating-point drift
            cubie.position.x = Math.sign(cubie.position.x || 0.001) * gapOffset;
            cubie.position.y = Math.sign(cubie.position.y || 0.001) * gapOffset;
            cubie.position.z = Math.sign(cubie.position.z || 0.001) * gapOffset;
            cubie.updateMatrixWorld(true);
          }

          this.scene.remove(pivot);
          this.isAnimating = false;
          resolve();

          // Process next queued move if any
          if (this.animationQueue.length > 0) {
            const next = this.animationQueue.shift();
            this.animateMove(next.moveName, next.durationMs).then(next.resolve);
          }
        }
      };

      requestAnimationFrame(animateStep);
    });
  }

  /**
   * Instantly reset all 8 cubies to the solved geometric positions & orientations.
   */
  resetToSolved() {
    this.animationQueue = [];
    this.isAnimating = false;
    const gapOffset = 0.52;
    for (let i = 0; i < 8; i++) {
      const cubie = this.cubies[i];
      if (cubie.parent !== this.cubeGroup) {
        this.cubeGroup.attach(cubie);
      }
      const [initX, initY, initZ] = SLOT_POSITIONS[i];
      cubie.position.set(initX * gapOffset * 2, initY * gapOffset * 2, initZ * gapOffset * 2);
      cubie.rotation.set(0, 0, 0);
      cubie.updateMatrix();
      cubie.updateMatrixWorld(true);
    }
  }

  /**
   * Instantly apply a 90-degree face rotation without animating frames.
   */
  applyMoveInstant(moveName) {
    const config = FACE_CONFIGS[moveName];
    if (!config) return;

    const movingCubies = [];
    const worldPos = new THREE.Vector3();
    for (const cubie of this.cubies) {
      cubie.getWorldPosition(worldPos);
      if (config.filter(worldPos)) {
        movingCubies.push(cubie);
      }
    }

    const pivot = new THREE.Group();
    this.scene.add(pivot);
    for (const cubie of movingCubies) {
      pivot.attach(cubie);
    }

    pivot.rotateOnAxis(config.axis, config.angle);
    pivot.updateMatrixWorld(true);

    const gapOffset = 0.52;
    for (const cubie of movingCubies) {
      this.cubeGroup.attach(cubie);
      cubie.position.x = Math.sign(cubie.position.x || 0.001) * gapOffset;
      cubie.position.y = Math.sign(cubie.position.y || 0.001) * gapOffset;
      cubie.position.z = Math.sign(cubie.position.z || 0.001) * gapOffset;
      cubie.updateMatrixWorld(true);
    }
    this.scene.remove(pivot);
  }

  /**
   * Instantly sync the 3D cube to match a complete sequence of moves from solved state.
   */
  setFromMoveSequence(moves) {
    this.resetToSolved();
    for (const m of moves) {
      this.applyMoveInstant(m);
    }
  }

  /**
   * Set cube orientation to match a given state by executing its moves,
   * or resetting and rapidly applying moves.
   */
  async applySequence(moves, durationPerMove = 200) {
    for (const m of moves) {
      await this.animateMove(m, durationPerMove);
    }
  }
}
