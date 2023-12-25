from asyncpg.pool import Pool


class Register:
    def __init__(self, pool: Pool):
        self.pool = pool
