class PushBoxGame:
    def __init__(self, map):
        self.map = map
        self.player_row = 0
        self.player_col = 0
        self.targets = []
        self.boxes = []
        self.target_count = 0
        self.is_game_over = False
        self.init_game()

    def init_game(self):
        for i, row in enumerate(self.map):
            for j, char in enumerate(row):
                if char == 'O':
                    self.player_row, self.player_col = i, j
                elif char == 'G':
                    self.targets.append((i, j))
                    self.target_count += 1
                elif char == 'X':
                    self.boxes.append((i, j))

    def check_win(self):
        for box in self.boxes:
            if box not in self.targets:
                return False
        self.is_game_over = True
        return True

    def move(self, direction):
        directions = {'w': (-1, 0), 's': (1, 0), 'a': (0, -1), 'd': (0, 1)}
        new_row, new_col = self.player_row + directions[direction][0], self.player_col + directions[direction][1]
        if 0 <= new_row < len(self.map) and 0 <= new_col < len(self.map[0]) and self.map[new_row][new_col] != '#':
            if (new_row, new_col) in self.boxes:
                box_new_row, box_new_col = new_row + directions[direction][0], new_col + directions[direction][1]
                if 0 <= box_new_row < len(self.map) and 0 <= box_new_col < len(self.map[0]) and self.map[box_new_row][box_new_col] != '#' and (box_new_row, box_new_col) not in self.boxes:
                    self.map[self.player_row][self.player_col] = ' '
                    self.map[new_row][new_col] = 'O'
                    self.map[box_new_row][box_new_col] = 'X'
                    self.player_row, self.player_col = new_row, new_col
                else:
                    return False
            else:
                self.map[self.player_row][self.player_col] = ' '
                self.map[new_row][new_col] = 'O'
                self.player_row, self.player_col = new_row, new_col
            return self.check_win()
        return False