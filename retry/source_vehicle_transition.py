"""Privileged source-physics reconstruction without rendering or a pixel actor.

This is a new Box2D world, not a simulator snapshot API. Observable body,
wheel, actuator and surface state is restored. Joint/contact warm-start
impulses, broadphase history and solver island ordering are not restored.
Only supplied controls are simulated; no future policy actions are inferred.
"""
import math
import time

import Box2D
import numpy as np

from core.vendor.car_dynamics import Car
from core.vendor.car_racing import VariablesContactDetector, FPS
from core.obstacle_contacts import ObstacleUserData, clear_obstacle_hit
from damage import CollisionDamage


BODY_FLAGS = ('linearDamping', 'angularDamping', 'gravityScale', 'bullet',
              'fixedRotation', 'sleepingAllowed', 'active', 'awake')
WORLD_FLAGS = ('warmStarting', 'continuousPhysics', 'subStepping', 'autoClearForces')


def body_state(body):
    return dict(position=list(body.position), angle=float(body.angle),
        velocity=list(body.linearVelocity), angular_velocity=float(body.angularVelocity),
        flags={key: getattr(body, key) for key in BODY_FLAGS})


def fixture_state(fixture):
    shape = fixture.shape
    geometry = (dict(vertices=[list(v) for v in shape.vertices]) if hasattr(shape, 'vertices')
                else dict(pos=list(shape.pos)))
    return dict(geometry=geometry, radius=float(shape.radius), density=float(fixture.density),
        friction=float(fixture.friction), restitution=float(fixture.restitution), sensor=bool(fixture.sensor),
        categoryBits=int(fixture.filterData.categoryBits), maskBits=int(fixture.filterData.maskBits),
        groupIndex=int(fixture.filterData.groupIndex))


def obstacle_contact_pair(contact, car, obstacles):
    """Stable fixture identity for gameplay contact history, not solver state."""
    car_bodies = (car.hull, *car.wheels)
    for obstacle_fixture, car_fixture in ((contact.fixtureA, contact.fixtureB),
                                          (contact.fixtureB, contact.fixtureA)):
        obstacle, body = obstacle_fixture.body, car_fixture.body
        if isinstance(obstacle.userData, ObstacleUserData) and any(body == b for b in car_bodies):
            return (next(i for i, o in enumerate(obstacles) if o == obstacle),
                    next(i for i, f in enumerate(obstacle.fixtures) if f == obstacle_fixture),
                    next(i for i, b in enumerate(car_bodies) if b == body),
                    next(i for i, f in enumerate(body.fixtures) if f == car_fixture))
    return None


def capture(env):
    """Read an actual pre-action boundary; never advance the source world."""
    raw = env.unwrapped
    assert raw.world.autoClearForces
    assert len(raw.world.bodies) == len(raw.road) + len(raw.obstacles) + 5
    wheels = []
    for wheel in raw.car.wheels:
        wheels.append(dict(body=body_state(wheel), tiles=sorted(int(t.idx) for t in wheel.tiles),
            dynamics={key: float(getattr(wheel, key)) for key in ('gas', 'brake', 'steer', 'omega', 'phase')},
            joint=dict(angle=float(wheel.joint.angle), reference_angle=float(wheel.joint.GetReferenceAngle()),
                motorSpeed=float(wheel.joint.motorSpeed), maxMotorTorque=float(wheel.joint.GetMaxMotorTorque()),
                limits=list(wheel.joint.limits), motorEnabled=bool(wheel.joint.motorEnabled),
                limitEnabled=bool(wheel.joint.limitEnabled))))
    return dict(hull=body_state(raw.car.hull), wheels=wheels,
        roads=[dict(body=body_state(t), fixture=fixture_state(t.fixtures[0]), idx=int(t.idx),
                    visited=bool(t.road_visited), friction=float(t.road_friction)) for t in raw.road],
        obstacles=[dict(body=body_state(o), fixture=fixture_state(o.fixtures[0]), hit=bool(o.userData.hit)) for o in raw.obstacles],
        touching_obstacle_contacts=sorted(pair for c in raw.world.contacts if c.touching
            and (pair := obstacle_contact_pair(c, raw.car, raw.obstacles)) is not None),
        world_flags={key: getattr(raw.world, key) for key in WORLD_FLAGS},
        grass_friction_multiplier=float(raw.car.grass_friction_multiplier),
        damage=float(env.damage.damage), off_track_counter=int(env.off_track_counter),
        unique_tiles=int(raw.tile_visited_count), road_count=len(raw.track),
        actual_time=float(raw.t), source_world_contacts=int(raw.world.contactCount),
        omitted='Warm-start joint/contact impulses, manifold/broadphase history and island order. Render/policy/finish-line state excluded. Forces are cleared at this actual wrapper boundary.')


def _restore_body(body, state):
    body.position, body.angle = state['position'], state['angle']
    body.linearVelocity, body.angularVelocity = state['velocity'], state['angular_velocity']
    for key, value in state['flags'].items():
        setattr(body, key, value)


def _static(world, specification):
    state, fixture = specification['body'], specification['fixture']
    body = world.CreateStaticBody(position=state['position'], angle=state['angle'])
    geo = fixture['geometry']
    shape = (Box2D.b2PolygonShape(vertices=geo['vertices']) if 'vertices' in geo
             else Box2D.b2CircleShape(pos=geo['pos'], radius=fixture['radius']))
    shape.radius = fixture['radius']
    body.CreateFixture(shape=shape, density=fixture['density'], friction=fixture['friction'],
        restitution=fixture['restitution'], isSensor=fixture['sensor'],
        filter=Box2D.b2Filter(categoryBits=fixture['categoryBits'], maskBits=fixture['maskBits'], groupIndex=fixture['groupIndex']))
    return body


class SourceVehicleTransition:
    """Source Car.step + Box2D constraints; no images, track generation or actor."""
    def __init__(self, snapshot):
        self.car = None
        self.track = [None] * snapshot['road_count']
        self.road_color = np.zeros(3)
        self.reward = 0.0
        self.tile_visited_count = snapshot['unique_tiles']
        self._collision_this_step = False
        self.contacts = set()
        self.listener = VariablesContactDetector(self, .95)
        self.world = Box2D.b2World((0, 0), contactListener=self.listener)
        for key, value in snapshot['world_flags'].items():
            setattr(self.world, key, value)
        self.roads, by_index = [], {}
        for spec in snapshot['roads']:
            tile = _static(self.world, spec)
            tile.userData = tile
            tile.idx, tile.road_visited, tile.road_friction = spec['idx'], spec['visited'], spec['friction']
            tile.color = np.zeros(3)
            self.roads.append(tile)
            by_index[tile.idx] = tile
        self.obstacles = []
        for spec in snapshot['obstacles']:
            obstacle = _static(self.world, spec)
            obstacle.userData = ObstacleUserData(hit=spec['hit'])
            self.obstacles.append(obstacle)
        origin = snapshot['hull']
        self.car = Car(self.world, origin['angle'], *origin['position'],
                       grass_friction_multiplier=snapshot['grass_friction_multiplier'])
        _restore_body(self.car.hull, origin)
        for wheel, state in zip(self.car.wheels, snapshot['wheels']):
            _restore_body(wheel, state['body'])
            for key, value in state['dynamics'].items():
                setattr(wheel, key, value)
            joint = state['joint']
            assert abs(wheel.joint.GetReferenceAngle() - joint['reference_angle']) < 1e-7
            wheel.joint.motorSpeed, wheel.joint.maxMotorTorque = joint['motorSpeed'], joint['maxMotorTorque']
            wheel.joint.limits = joint['limits']
            wheel.joint.motorEnabled, wheel.joint.limitEnabled = joint['motorEnabled'], joint['limitEnabled']
            wheel.tiles = {by_index[index] for index in state['tiles']}
        old_contact = self.listener._contact

        self._constructing_contacts = True
        self._initial_contact_events = []

        def contact(c, begin):
            if self._constructing_contacts:
                # Build manifolds without advancing the game's event history.
                self._initial_contact_events.append((c, begin))
                return
            if begin:
                body = self.listener._match_obstacle_contact(c)
                if body is not None:
                    self.contacts.update(i for i, o in enumerate(self.obstacles) if o == body)
            return old_contact(c, begin)

        self.listener._contact = contact
        self.damage = CollisionDamage()
        self.damage.damage = snapshot['damage']
        self._effects()
        self.off_track_counter = snapshot['off_track_counter']
        self.native_ticks = 0
        # Zero time constructs only contact structure. Gameplay callbacks wait
        # until the collision phase of the first positive-time physics step.
        self.world.Step(0., 180, 60)
        self._constructing_contacts = False
        self._restored_obstacle_contacts = {tuple(p) for p in snapshot.get('touching_obstacle_contacts', [])}
        geometric_obstacle_contacts = {pair for c, begin in self._initial_contact_events
            if begin and (pair := obstacle_contact_pair(c, self.car, self.obstacles)) is not None}
        self._initial_obstacle_ends = (sorted(self._restored_obstacle_contacts - geometric_obstacle_contacts)
            if 'touching_obstacle_contacts' in snapshot else [])
        self._initial_geometric_tiles = [set() for _ in self.car.wheels]
        for c, begin in self._initial_contact_events:
            assert begin, 'New world unexpectedly emitted an initial EndContact'
            first, second = c.fixtureA.body.userData, c.fixtureB.body.userData
            for tile, wheel in ((first, second), (second, first)):
                if (tile and 'road_friction' in tile.__dict__ and wheel
                        and 'tiles' in wheel.__dict__):
                    index = next(i for i, w in enumerate(self.car.wheels) if w == wheel)
                    self._initial_geometric_tiles[index].add(tile)
        self.initial_event_receipt = dict(
            deferred_begin_callbacks=len(self._initial_contact_events),
            restored_obstacle_end_callbacks=len(self._initial_obstacle_ends),
            suppressed_existing_obstacle_begin_callbacks=len(self._restored_obstacle_contacts & geometric_obstacle_contacts),
            deferred_road_contact_additions=sum(len(now - w.tiles) for w, now in
                                                zip(self.car.wheels, self._initial_geometric_tiles)),
            deferred_road_contact_removals=sum(len(w.tiles - now) for w, now in
                                               zip(self.car.wheels, self._initial_geometric_tiles)),
            counter_offset_correction=0)
        self._initial_events_pending = True
        # Joint motor setters wake attached bodies during reconstruction.
        # Restore captured sleep state after joint and zero-time contact setup.
        for body, state in [(self.car.hull, snapshot['hull'])] + [
                (wheel, item['body']) for wheel, item in zip(self.car.wheels, snapshot['wheels'])]:
            body.awake = state['flags']['awake']
        self.initial_tiles_exact = ([sorted(int(t.idx) for t in w.tiles) for w in self.car.wheels]
                                    == [w['tiles'] for w in snapshot['wheels']])
        self.initial_progress_exact = self.tile_visited_count == snapshot['unique_tiles']
        self.initial_bodies_exact = (body_state(self.car.hull) == snapshot['hull'] and all(
            body_state(w) == state['body'] for w, state in zip(self.car.wheels, snapshot['wheels'])))
        self.contacts.clear()

    def _effects(self):
        effect = self.damage.effects
        self.car.set_damage_effects(effect.grip_multiplier, effect.engine_multiplier, effect.steering_multiplier)

    def step(self, action):
        action = np.asarray(action, dtype=np.float64)
        assert action.shape == (3,) and np.isfinite(action).all()
        before_tiles = self.tile_visited_count
        collision = False
        self.contacts.clear()
        for _ in range(4):
            self._collision_this_step = False
            self.car.steer(-action[0])
            self.car.gas(action[1])
            self.car.brake(action[2])
            self.car.step(1. / FPS)
            if self._initial_events_pending:
                # Car.step has just used the captured, previous-step tile set,
                # exactly as in CarRacing.step. Reconcile contacts now, before
                # the first positive-time world solve. Existing contact pairs
                # that disappeared need the corresponding removal as well.
                for wheel, geometric in zip(self.car.wheels, self._initial_geometric_tiles):
                    wheel.tiles.intersection_update(geometric)
                # A captured touching pair absent in the fresh geometric world
                # would end at the next collision phase. Preserve its source
                # EndContact bookkeeping, including clearing the hit flag.
                for pair in self._initial_obstacle_ends:
                    clear_obstacle_hit(self.obstacles[pair[0]])
                self._initial_obstacle_ends.clear()
                for contact, begin in self._initial_contact_events:
                    pair = obstacle_contact_pair(contact, self.car, self.obstacles)
                    if pair is not None and pair in self._restored_obstacle_contacts:
                        # Reconstructing a persistent pair is not a new begin.
                        continue
                    self.listener._contact(contact, begin)
                self._initial_contact_events.clear()
                self._initial_events_pending = False
            self.world.Step(1. / FPS, 180, 60)
            self.native_ticks += 1
            collision |= bool(self._collision_this_step)
        crashed = self.damage.update(collision)
        self._effects()
        # Source reward is 1000/N per new tile minus .1 per raw tick.
        # For N<2500, at least one new tile makes this wrapper reward positive.
        assert len(self.track) < 2500
        self.off_track_counter = self.off_track_counter + 1 if self.tile_visited_count == before_tiles else 0
        hull = self.car.hull
        return dict(position=list(hull.position), angle=float(hull.angle), velocity=list(hull.linearVelocity),
            angular_velocity=float(hull.angularVelocity), speed_m_s=math.hypot(*hull.linearVelocity),
            unique_tiles=self.tile_visited_count, damage=self.damage.damage, off_track_counter=self.off_track_counter,
            wheel_road_contacts=sum(bool(w.tiles) for w in self.car.wheels), collision=collision,
            contact_obstacle_ids=sorted(self.contacts), terminal=bool(crashed or self.off_track_counter > 100))

    def close(self):
        self.world.contactListener = None
        self.listener.env = None


def controls(anchor, specification):
    """Reproduce the preregistered macro from its current-action anchor only."""
    anchor = np.asarray(anchor, np.float32)
    result = []
    for phase in range(2):
        action = anchor.copy()
        if 'explicit_pedals' in specification:
            action[1:] = specification['explicit_pedals']
        action[0] = np.clip(float(anchor[0]) + specification['steer_offsets'][phase], -.4, .4)
        if phase == 0 and specification['brake_first_block']:
            action[1:] = (0., specification['brake_value'])
        result.extend([action.copy() for _ in range(specification['block_actions'])])
    return result


def predict(snapshot, anchor, specifications):
    start = time.perf_counter()
    result = {}
    for name, spec in specifications.items():
        before = time.perf_counter()
        model = SourceVehicleTransition(snapshot)
        reconstruction_wall = time.perf_counter() - before
        restored = dict(tiles=model.initial_tiles_exact, progress=model.initial_progress_exact,
                        bodies=model.initial_bodies_exact)
        rows = []
        integration_start = time.perf_counter()
        try:
            for action in controls(anchor, spec):
                row = model.step(action)
                rows.append(row)
                if row['terminal']:
                    break
        finally:
            model.close()
        result[name] = dict(rows=rows, initialization=restored, wall_s=time.perf_counter() - before,
                            reconstruction_wall_s=reconstruction_wall,
                            integration_wall_s=time.perf_counter() - integration_start,
                            event_initialization=model.initial_event_receipt,
                            model_physics_ticks=model.native_ticks, zero_time_contact_initializations=1)
    return dict(candidates=result, batch_wall_s=time.perf_counter() - start,
        model_physics_ticks=sum(r['model_physics_ticks'] for r in result.values()),
        native_environment_steps=0, snapshot_API_used=False, future_actor_calls=0)
