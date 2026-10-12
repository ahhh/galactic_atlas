/**
 * Orbiting camera rig with eased fly-to.
 *
 * The rig keeps the camera on a sphere around a target point, described by
 * a distance and two angles. Every navigation action -- a search result, a
 * click, a breadcrumb -- becomes a `flyTo` towards a new (target, distance,
 * angles) tuple, which is what makes travel feel continuous rather than a
 * jump cut.
 *
 * Controls are implemented here rather than pulled from OrbitControls so
 * that a user drag can interrupt an in-flight animation cleanly.
 */

import * as THREE from '../vendor/three.module.js';

const MIN_ELEVATION = -Math.PI / 2 + 0.02;
const MAX_ELEVATION = Math.PI / 2 - 0.02;

/** Cubic ease-in-out: slow departure, fast cruise, gentle arrival. */
function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

/** Shortest signed angular difference, so the camera never takes the long way. */
function shortestAngle(from, to) {
  let delta = (to - from) % (Math.PI * 2);
  if (delta > Math.PI) delta -= Math.PI * 2;
  if (delta < -Math.PI) delta += Math.PI * 2;
  return delta;
}

export class CameraRig {
  constructor(camera, domElement) {
    this.camera = camera;
    this.domElement = domElement;

    this.target = new THREE.Vector3();
    this.distance = 10;
    this.azimuth = Math.PI * 0.25;
    this.elevation = Math.PI * 0.18;

    this.minDistance = 1e-4;
    this.maxDistance = 1e6;
    this.rotateSpeed = 0.0045;
    this.panSpeed = 1.0;
    this.zoomSpeed = 0.0016;
    this.damping = 0.12;

    // Smoothed values the camera actually follows.
    this._target = this.target.clone();
    this._distance = this.distance;
    this._azimuth = this.azimuth;
    this._elevation = this.elevation;

    this.flight = null;
    this.enabled = true;
    this._pointers = new Map();
    this._lastPinch = 0;
    this._onChange = null;

    this._bindEvents();
  }

  onChange(callback) { this._onChange = callback; }

  /** Immediately place the rig, with no animation. */
  set({ target, distance, azimuth, elevation }) {
    if (target) { this.target.copy(target); this._target.copy(target); }
    if (distance !== undefined) { this.distance = distance; this._distance = distance; }
    if (azimuth !== undefined) { this.azimuth = azimuth; this._azimuth = azimuth; }
    if (elevation !== undefined) { this.elevation = elevation; this._elevation = elevation; }
    this.flight = null;
    this._apply();
  }

  /**
   * Animate to a new vantage point.
   *
   * Distance is interpolated geometrically (in log space) because these
   * moves routinely span several orders of magnitude, and a linear
   * interpolation would spend almost the whole animation at the far end.
   */
  flyTo({ target, distance, azimuth, elevation, duration = 1600, onArrive = null }) {
    const from = {
      target: this._target.clone(),
      distance: this._distance,
      azimuth: this._azimuth,
      elevation: this._elevation,
    };
    const to = {
      target: target ? target.clone() : from.target.clone(),
      distance: distance !== undefined ? Math.max(this.minDistance, distance) : from.distance,
      azimuth: azimuth !== undefined ? from.azimuth + shortestAngle(from.azimuth, azimuth) : from.azimuth,
      elevation: elevation !== undefined ? elevation : from.elevation,
    };
    this.flight = { from, to, start: performance.now(), duration, onArrive };
    return this.flight;
  }

  /** True while a fly-to is running. */
  get isFlying() { return this.flight !== null; }

  cancelFlight() { this.flight = null; }

  update() {
    if (this.flight) {
      const { from, to, start, duration, onArrive } = this.flight;
      const elapsed = performance.now() - start;
      const t = duration <= 0 ? 1 : Math.min(1, elapsed / duration);
      const eased = easeInOutCubic(t);

      this._target.lerpVectors(from.target, to.target, eased);
      // Geometric interpolation across scale changes.
      this._distance = from.distance * Math.pow(to.distance / from.distance, eased);
      this._azimuth = from.azimuth + (to.azimuth - from.azimuth) * eased;
      this._elevation = from.elevation + (to.elevation - from.elevation) * eased;

      this.target.copy(this._target);
      this.distance = this._distance;
      this.azimuth = this._azimuth;
      this.elevation = this._elevation;

      if (t >= 1) {
        this.flight = null;
        if (onArrive) onArrive();
      }
    } else {
      // Critically-damped-ish approach to the user-controlled values.
      const k = this.damping;
      this._target.lerp(this.target, k);
      this._distance += (this.distance - this._distance) * k;
      this._azimuth += (this.azimuth - this._azimuth) * k;
      this._elevation += (this.elevation - this._elevation) * k;
    }
    this._apply();
  }

  _apply() {
    const cosElevation = Math.cos(this._elevation);
    const offset = new THREE.Vector3(
      this._distance * cosElevation * Math.cos(this._azimuth),
      this._distance * Math.sin(this._elevation),
      this._distance * cosElevation * Math.sin(this._azimuth),
    );
    this.camera.position.copy(this._target).add(offset);
    this.camera.lookAt(this._target);
    if (this._onChange) this._onChange(this);
  }

  /** Distance from the camera to its target, in scene units. */
  get currentDistance() { return this._distance; }

  // --- Input ---------------------------------------------------------------

  _bindEvents() {
    const element = this.domElement;
    element.style.touchAction = 'none';

    element.addEventListener('pointerdown', (event) => {
      if (!this.enabled) return;
      element.setPointerCapture(event.pointerId);
      this._pointers.set(event.pointerId, { x: event.clientX, y: event.clientY, button: event.button });
      this._dragged = false;
    });

    element.addEventListener('pointermove', (event) => {
      if (!this.enabled) return;
      const pointer = this._pointers.get(event.pointerId);
      if (!pointer) return;
      const dx = event.clientX - pointer.x;
      const dy = event.clientY - pointer.y;
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      if (Math.abs(dx) + Math.abs(dy) > 2) this._dragged = true;

      if (this._pointers.size === 2) {
        this._handlePinch();
        return;
      }
      // A deliberate drag takes over from any animation in progress.
      this.cancelFlight();
      const panning = pointer.button === 2 || pointer.button === 1 || event.shiftKey;
      if (panning) this._pan(dx, dy);
      else this._rotate(dx, dy);
    });

    const release = (event) => {
      this._pointers.delete(event.pointerId);
      if (this._pointers.size < 2) this._lastPinch = 0;
    };
    element.addEventListener('pointerup', release);
    element.addEventListener('pointercancel', release);
    element.addEventListener('contextmenu', (event) => event.preventDefault());

    element.addEventListener('wheel', (event) => {
      if (!this.enabled) return;
      event.preventDefault();
      this.cancelFlight();
      this.zoomBy(event.deltaY);
    }, { passive: false });
  }

  _rotate(dx, dy) {
    this.azimuth -= dx * this.rotateSpeed;
    this.elevation = Math.max(MIN_ELEVATION,
      Math.min(MAX_ELEVATION, this.elevation + dy * this.rotateSpeed));
  }

  _pan(dx, dy) {
    // Pan in the camera's own plane, scaled so the world tracks the cursor
    // at roughly one-to-one regardless of zoom level.
    const scale = this._distance * 0.0022 * this.panSpeed;
    const right = new THREE.Vector3();
    const up = new THREE.Vector3();
    this.camera.matrixWorld.extractBasis(right, up, new THREE.Vector3());
    this.target.addScaledVector(right, -dx * scale);
    this.target.addScaledVector(up, dy * scale);
  }

  _handlePinch() {
    const points = Array.from(this._pointers.values());
    const separation = Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y);
    if (this._lastPinch) {
      this.cancelFlight();
      this.zoomBy((this._lastPinch - separation) * 3);
    }
    this._lastPinch = separation;
  }

  zoomBy(delta) {
    const factor = Math.exp(delta * this.zoomSpeed);
    this.distance = Math.min(this.maxDistance, Math.max(this.minDistance, this.distance * factor));
  }

  /** Did the last pointer interaction move far enough to count as a drag? */
  get wasDragged() { return this._dragged === true; }
}

export { easeInOutCubic };
