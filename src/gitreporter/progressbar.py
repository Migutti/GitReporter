class ProgressBar():
    def __init__(self, name='Progress', max_value=0):
        self.name = name
        self.current_value = 0
        self.max_value = max_value

    def __enter__(self):
        print(f'{self.name}: {self.current_value}/{self.max_value} [                    ]', end='')
        return self

    def increment(self):
        previous_progress = int(20 * self.current_value / self.max_value)
        self.current_value += 1
        progress = int(20 * self.current_value / self.max_value)
        if progress <= previous_progress:
            return
        print(f'\r{self.name}: {self.current_value}/{self.max_value} [{progress * "="}{" " * (20 - progress)}]', end='')

    def __exit__(self, *_):
        print(f'\r{self.name}: {self.current_value}/{self.max_value} [====================]')
