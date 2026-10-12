/**
 * Renderer, per-mode scenes, label overlay and scale transitions.
 *
 * Each view mode owns its own THREE.Scene with its own units (kly for the
 * galaxy, schematic units for a system, planetary radii up close). Moving
 * between them is a veiled cut rather than a literal traversal.
 */

import * as THREE from '../vendor/three.module.js';
import { MODES } from './constants.js';

export class SceneManager {
  constructor(canvas, veilElement, labelLayer) {
    this.canvas = canvas;
    this.veil = veilElement;
    this.labelLayer = labelLayer;

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
    this.renderer.setClearColor(0x030409, 1);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    this.camera = new THREE.PerspectiveCamera(50, 1, 0.01, 2000);
    this.scenes = new Map();
    for (const mode of Object.values(MODES)) {
      const scene = new THREE.Scene();
      scene.userData.mode = mode;
      this.scenes.set(mode, scene);
    }
    this.mode = MODES.GALAXY;
    this._labels = new Map();
    this._buildBackdrop();
    this.resize();
  }

  /** A faint, fixed star field shared by every scene, for continuity. */
  _buildBackdrop() {
    const count = 2400;
    const positions = new Float32Array(count * 3);
    let seed = 41000;
    const random = () => {
      seed = (seed * 1664525 + 1013904223) % 4294967296;
      return seed / 4294967296;
    };
    for (let i = 0; i < count; i += 1) {
      const u = random() * 2 - 1;
      const theta = random() * Math.PI * 2;
      const r = Math.sqrt(1 - u * u);
      positions.set([r * Math.cos(theta), u, r * Math.sin(theta)], i * 3);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    this.backdrop = new THREE.Points(geometry, new THREE.PointsMaterial({
      color: 0xb8c4dc, size: 1.2, sizeAttenuation: false, transparent: true, opacity: 0.4,
      depthWrite: false, depthTest: false,
    }));
    this.backdrop.frustumCulled = false;
    this.backdrop.renderOrder = -1000;
  }

  scene(mode = this.mode) { return this.scenes.get(mode); }

  setMode(mode) { this.mode = mode; }

  resize() {
    const width = this.canvas.clientWidth || window.innerWidth;
    const height = this.canvas.clientHeight || window.innerHeight;
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
  }

  render() {
    const scene = this.scene();
    if (this.backdrop.parent !== scene) scene.add(this.backdrop);
    this.backdrop.position.copy(this.camera.position);
    this.backdrop.scale.setScalar(this.camera.far * 0.5);
    this.renderer.render(scene, this.camera);
  }

  /** Run a veiled transition; `swap` runs while the screen is dark. */
  async transition(swap, { inDuration = 380, holdDuration = 80, outDuration = 480 } = {}) {
    this.transitioning = true;
    this.veil.classList.add('is-active');
    await wait(inDuration);
    await swap();
    await wait(holdDuration);
    this.veil.classList.remove('is-active');
    await wait(outDuration);
    this.transitioning = false;
  }

  /**
   * Project label anchors into the HTML overlay. Entries marked `centred`
   * sit over their anchor; the rest sit just to the right of a marker.
   */
  updateLabels(entries) {
    const seen = new Set();
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;
    const projected = new THREE.Vector3();
    for (const entry of entries) {
      projected.copy(entry.position).project(this.camera);
      if (projected.z > 1 || Math.abs(projected.x) > 1.2 || Math.abs(projected.y) > 1.2) continue;
      seen.add(entry.id);
      let element = this._labels.get(entry.id);
      if (!element) {
        element = document.createElement('button');
        element.type = 'button';
        this.labelLayer.appendChild(element);
        this._labels.set(entry.id, element);
      }
      element.onclick = (event) => {
        event.stopPropagation();
        entry.onSelect?.();
      };
      if (element.dataset.text !== entry.text) {
        element.textContent = entry.text;
        element.dataset.text = entry.text;
      }
      const centred = entry.centred || /is-(segmentum|region|era|warp|sector|event)/.test(entry.className || '');
      element.className = `space-label ${entry.className || ''}${entry.onSelect ? '' : ' is-static'}`;
      const sx = (projected.x * 0.5 + 0.5) * width;
      const sy = (-projected.y * 0.5 + 0.5) * height + (entry.offsetY || 0);
      element.style.transform = centred
        ? `translate(-50%, -50%) translate(${sx}px, ${sy}px)`
        : `translate(10px, -50%) translate(${sx}px, ${sy}px)`;
    }
    for (const [id, element] of this._labels) {
      if (!seen.has(id)) {
        element.remove();
        this._labels.delete(id);
      }
    }
  }

  clearLabels() {
    for (const element of this._labels.values()) element.remove();
    this._labels.clear();
  }

  pointerToNdc(event) {
    const rect = this.canvas.getBoundingClientRect();
    return new THREE.Vector2(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      -((event.clientY - rect.top) / rect.height) * 2 + 1,
    );
  }
}

export function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
