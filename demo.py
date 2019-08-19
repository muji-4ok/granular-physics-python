import random
import pygame as p
import argparse

WIDTH = 800
HEIGHT = 800
BLOCK_SIZE = 10
COLS = HEIGHT // BLOCK_SIZE
ROWS = WIDTH // BLOCK_SIZE
SIZE = WIDTH, HEIGHT
UPDATE_DELAY = 0
NEW_DELAY = 3
BIG_PROBABILITY = 0.2
FPS = 0


class World(dict):
    def __init__(self, cols: int, rows: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cols = cols
        self.rows = rows


class Particle:
    size = 0
    color = 0, 0, 0

    def __init__(self, i: int, j: int, world: World):
        self.i = i
        self.j = j
        self.world = world
        self.static = False

        for di in range(self.size):
            for dj in range(self.size):
                world[(i + di, j + dj)] = self

    def update(self):
        if self.static:
            return False

        down = self.go_down()

        if down:
            return True
        else:
            down_right = self.go_down_right()

            if down_right:
                return True
            else:
                self.static = True
                return False

    def replace(self, i: int, j: int):
        for di in range(self.size):
            for dj in range(self.size):
                if i + di >= self.world.rows or j + dj >= self.world.cols:
                    return False

                query = self.world.get((i + di, j + dj), None)

                if query is not None and query != self:
                    return False

        for di in range(self.size):
            for dj in range(self.size):
                self.world[(self.i + di, self.j + dj)] = None

        for di in range(self.size):
            for dj in range(self.size):
                self.world[(i + di, j + dj)] = self

        self.i = i
        self.j = j

        return True

    def go_down(self):
        return self.replace(self.i + 1, self.j)

    def go_down_right(self):
        return self.replace(self.i + 1, self.j + 1)


class ParticleBig(Particle):
    size = 2
    color = 255, 0, 0


class ParticleSmall(Particle):
    size = 1
    color = 0, 255, 0


class Game:
    def __init__(self, width: int, height: int, block_size: int, update_delay: int, new_delay: int,
                 big_probability: float, fps: int):
        self.fps = fps
        self.big_probability = big_probability
        self.block_size = block_size

        if width % block_size:
            raise ValueError('width must be divisible by block size')

        rows = width // block_size

        if height % block_size:
            raise ValueError('height must be divisible by block size')

        cols = height // block_size

        if update_delay >= new_delay or (update_delay and new_delay % update_delay):
            raise ValueError('new delay must be bigger than update delay and divisible by it')

        self.update_delay = update_delay
        self.new_delay = new_delay

        size = width, height
        p.init()
        self.screen = p.display.set_mode(size)
        p.display.set_caption('Granular physics')
        self.world = World(cols, rows)
        self.particles = set()
        self.clock = p.time.Clock()
        # Numbers of drawn frames
        self.cycles = 0
        self.cycles_passed_update = 0
        self.cycles_passed_new = 0
        self.drop_j = 0
        self.running = True

    def can_place(self, i: int, j: int, size: int):
        for di in range(size):
            for dj in range(size):
                if i + di >= self.world.rows or j + dj >= self.world.cols:
                    return False

                query = self.world.get((i + di, j + dj), None)

                if query is not None:
                    return False

        return True

    def update(self):
        for event in p.event.get():
            if event.type == p.QUIT:
                quit()

        if not self.running:
            self.clock.tick(10)
            return

        self.screen.fill((0, 0, 0))

        for i in range(self.world.rows):
            for j in range(self.world.cols):
                particle = self.world.get((i, j), None)

                if particle is not None:
                    p.draw.rect(self.screen, particle.color, (j * self.block_size,
                                                              i * self.block_size,
                                                              self.block_size,
                                                              self.block_size))
                else:
                    pass

        p.display.flip()

        if self.cycles >= self.cycles_passed_update + self.update_delay:
            self.cycles_passed_update = self.cycles
            to_be_deleted = []

            for particle in self.particles:
                if not particle.update():
                    to_be_deleted.append(particle)

            for particle in to_be_deleted:
                self.particles.remove(particle)

        if self.cycles >= self.cycles_passed_new + self.new_delay:
            self.cycles_passed_new = self.cycles
            particle = None

            if random.random() < self.big_probability:
                if self.can_place(0, self.drop_j, 2):
                    particle = ParticleBig(0, self.drop_j, self.world)
                else:
                    self.drop_j += 1
            else:
                if self.can_place(0, self.drop_j, 1):
                    particle = ParticleSmall(0, self.drop_j, self.world)
                else:
                    self.drop_j += 1

            if particle is not None:
                self.particles.add(particle)

        self.cycles += 1

        if self.drop_j >= self.world.cols:
            self.running = False

        self.clock.tick(self.fps)

    def run(self):
        while True:
            self.update()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Demo of falling big and small blocks')

    parser.add_argument('width', nargs='?', type=int, default=WIDTH, help='Width of window (default: %(default)s)')
    parser.add_argument('height', nargs='?', type=int, default=HEIGHT, help='Height of window (default: %(default)s)')
    parser.add_argument(
        'block_size', nargs='?', type=int, default=BLOCK_SIZE,
        help='Size of the small block, width and height must be divisible by this (default: %(default)s)'
    )
    parser.add_argument('--update', '-u', required=False, type=int, default=UPDATE_DELAY,
                        help='Delay between block updates in frames (default: %(default)s)')
    parser.add_argument('--new', '-n', required=False, type=int, default=NEW_DELAY,
                        help='Delay between creation of new block in frames (default: %(default)s)')
    parser.add_argument('--big-probability', '-p', required=False, type=float, default=BIG_PROBABILITY,
                        help='Probability of creating a big block [from 0.0 to 1.0] (default: %(default)s)')
    parser.add_argument('--cap-fps', '-f', required=False, type=int, default=FPS,
                        help='If specified, cap fps. It is uncapped otherwise')

    args = parser.parse_args()

    if args.big_probability < 0 or args.big_probability > 1:
        raise ValueError('probability must be between 0.0 and 1.0')

    g = Game(args.width, args.height, args.block_size, args.update, args.new, args.big_probability, args.cap_fps)
    g.run()
