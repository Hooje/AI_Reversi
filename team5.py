
import STcpClient
import random
import time
import copy
import math
'''
    輪到此程式移動棋子
    board : 棋盤狀態(list of list), board[i][j] = i row, j column 棋盤狀態(i, j 從 0 開始)
            0 = 空、1 = 黑、2 = 白、-1 = 四個角落
    is_black : True 表示本程式是黑子、False 表示為白子
 
    return Step
    Step : single touple, Step = (r, c)
            r, c 表示要下棋子的座標位置 (row, column) (zero-base)
'''

dh=[-1, -1, -1, 0, 0, 1, 1, 1]
dw=[-1, 0, 1, -1, 1, -1, 0, 1]

def valid(h, w):
    if (h>=0 and h<=7 and w>=0 and  w<=7):
        return True
    return False

class Board():
    global mystate
    """
    board for handling the game
    """
    def __init__(self, board, is_black=True):
        self.width = 8
        self.height = 8
        self.is_black = is_black
        self.states = board
        self.availables = [] # 棋盤上可以下的位置（下了之後可以翻動對手的棋）
        self.remain = [] # 還沒下過的空格
        self.get_available()
 
    def move_to_location(self, move): # move 從0~63 
        """
        move 從0~63 :
        0  1  2  3  4  5  6  7
        8  9 10 11 12 13 14 15
        ...
 
        把他轉成座標點
        """
        h = move  // self.width # 用//取整數
        w = move  %  self.width 
        return h, w
 
    def location_to_move(self, location): #座標轉move
        if(len(location) != 2): 
            return -1
        h = location[0]
        w = location[1]
        move = h * self.width + w
        if(move not in range(self.width * self.height)):
            return -1
        return move
 
    def flip(self, move): # 判斷下了棋之後 有哪些棋子要被翻轉
        global dh, dw
        h, w = self.move_to_location(move)

        for i in range(8):
            flip=False  #要不要翻
            k=1 #某方向走幾次
            if valid(h+dh*k, w+dw*k):
                if (self.states[h+dh*k][w+dw*k]==mystate): #若某方向的第一個就是自己的，就算了
                    continue
                while (self.states[h+dh*k][w+dw*k]!=0) : #某方向為敵隊(因為不為空，也不是自己)，就一直走下去直到找到自己
                    flip=True #若沒有遇到敵隊，隔壁就是空位，那也不能翻
                    k+=1
                    if not valid(h+dh, w+dw): #某方向全是敵隊，就算了
                        continue 
                if (self.states[h+dh*k][w+dw*k]==mystate) and (flip==True): #找到自己，而且剛剛有遇到敵隊
                    k-=1
                    while (self.states[h+dh*k][w+dw*k]!=mystate): #從最遠的敵隊翻回最新下的這個點
                        self.states[h+dh*k][w+dw*k]=mystate
                        k-=1

    def can_flip(self, move): # 判斷下了棋之後 有哪些棋子要被翻轉
        global dh, dw
        h, w = self.move_to_location(move)

        for i in range(8):
            flip=False  #要不要翻
            k=1 #某方向走幾次
            if valid(h+dh*k, w+dw*k):
                if (self.states[h+dh*k][w+dw*k]==mystate): #若某方向的第一個就是自己的，就算了
                    continue
                while (self.states[h+dh*k][w+dw*k]!=0) : #某方向為敵隊(因為不為空，也不是自己)，就一直走下去直到找到自己
                    flip=True #若沒有遇到敵隊，隔壁就是空位，那也不能翻
                    k+=1
                    if not valid(h+dh, w+dw): #某方向全是敵隊，就算了
                        continue 
                if (self.states[h+dh*k][w+dw*k]==mystate) and (flip==True): #找到自己，而且剛剛有遇到敵隊
                    return True
        return False

    def get_available(self): #從空格找出可以下的步(可以翻對面的棋的步才可以走)
        for i in range(64):
            h, w = self.move_to_location(i)
            if h == 0 or w == 0 or h == 7 or w == 7: #在邊界的話
                if self.states[h][w] != 0: # 這格已經有棋子了，就跳過
                    continue
                if self.can_flip(i):
                    self.availables.append(i) # 這格可以走，把他加入available
            else:
                if self.states[h][w] == 0: # 這格已經有棋子了就跳過
                    self.availables.append(i)

    def update(self, player, move): # player在move处落子，更新棋盘
        self.states[move] = player
        self.get_available()

class MCTS(object):
    global mystate
    """
    下棋AI算法，用蒙地卡羅樹搜尋
    """
 
    def __init__(self, board, play_turn, time=5, max_actions=1000): #這個board是上面的class
        """
        參數可以改改看 搞不好會比較牛逼
        """
        self.board = board
        self.play_turn = play_turn 
        self.calculation_time = float(time) # 最多算多久(預設五秒)
        self.max_actions = max_actions # 最多要模擬幾步(預設1000步)
        self.confident = 1.96 # 決定expand或是exploit的強弱的常數
        self.player = play_turn[0] #一開始都是我們先出手
        self.plays = {} # 用(player, move)來記
        self.wins = {} # 記獲勝次數
        self.max_depth = 1 # 一次只能expand一層走法
        
    def get_action(self): # 回傳一個move
        if len(self.board.availables == 1): #只剩最後一格可以下，直接回傳那格
            return self.board.remain[0]
        # 得到新的棋盤的時候，都要清空前面的紀錄
        self.plays = {} 
        self.wins = {}
        simulations = 0
        begin = time.time()
        while time.time() - begin < self.calculation_time:
            board_copy = copy.deepcopy(self.board)  # 做call by value
            play_turn_copy = copy.deepcopy(self.play_turn)
            self.run_simulation(board_copy, play_turn_copy) # 做MCTS
            simulations += 1
 
        move = self.select_one_move() # 選一個最好的走法
        h, w = self.board.move_to_location(move)

        return h, w

    def get_player(self, players):
        p = players.pop(0)
        players.append(p)
        return p 

    def run_simulation(self, board, play_turn):
        """
        MCTS main process
        """

        plays = self.plays
        wins = self.wins
        availables = board.availables

        player = self.get_player(play_turn) # 現在換誰下？
        visited_states = set() # 紀錄被selected的路徑上的所有走法
        winner = -1
        expand = True

        # Simulation
        for t in range(1, self.max_actions + 1):
            # Selection
            # 如果都有統計資料，那就走UCB最大的
            if all(plays.get((player, move)) for move in availables):
                log_total = math.log(
                    sum(plays[(player, move)] for move in availables))
                value, move = max(
                    ((wins[(player, move)] / plays[(player, move)]) +
                     math.sqrt(self.confident * log_total / plays[(player, move)]), move)
                    for move in availables) 
            else:
                # 不然就隨便挑個走
                move = random.choice(availables)

            board.update(player, move)

            # Expand
            # 一次模擬最多Expand一層
            if expand and (player, move) not in plays:
                expand = False
                plays[(player, move)] = 0
                wins[(player, move)] = 0
                if t > self.max_depth:
                    self.max_depth = t

            visited_states.add((player, move))

            is_full = not len(availables)
            win, winner = self.has_a_winner(board)
            if is_full or win: # 遊戲結束
                break

            player = self.get_player(play_turn)

        # Back-propagation
        for player, move in visited_states:
            if (player, move) not in plays:
                continue
            plays[(player, move)] += 1 # 走過的次數都+1
            if player == winner:
                wins[(player, move)] += 1 # 勝利的玩家wins +1
 
    def select_one_move(self):
        percent_wins, move = max(
            (self.wins.get((self.player, move), 0) /
             self.plays.get((self.player, move), 1),
             move)
            for move in self.board.availables) # 選一個勝率最高的走法

        return move

    def has_a_winner(self, board):
        count_black = 0
        count_white = 0
        if len(board.availables) == 0: #沒有地方可以下了
            for h in range(8):
                for w in range(8):
                    if self.board.states[h][w] == 1:
                        count_black += 1   
                    elif self.board.states[h][w] == 2:
                        count_white += 1
            if count_black > count_white:
                return True, 1 #黑棋比較多，贏了
            else:
                return True, 2
        else:
            return False, -1 #遊戲還沒結束
    '''
     The game ends when neither player has any remaining legal move.
     At the end, the score of a player is the number of pieces in his/her color minus the number of pieces in
    the opponent's color. It is possible for the game to end in a tie.
    '''
 

def GetStep(board, is_black):
    global mystate
    mystate=((is_black+1)%2)+1  # isblack=1 --> mystate=1   isblack=0 --> mystate=2
    
    if is_black==1 :
        play_turn=[1, 0]
    else:
        play_turn=[0, 1]
    '''
    board_class= MCTS(board, play_turn)
    x, y= board_class.get_action()
    '''
    x = random.randint(0, 7)
    y = random.randint(0, 7)
    
    return (x,y)

first_time = True

while(True):
    (stop_program, id_package, board, is_black) = STcpClient.GetBoard()
    '''
    if first_time:
        #ai = MCTS(board_class,1000)
        first_time = False
    '''
    if(stop_program):
        break
    
    Step = GetStep(board, is_black)
    STcpClient.SendStep(id_package, Step)



