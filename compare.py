import STcpClient1
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
#        self.get_available()
#        self.get_remain()
 
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
 
    def flip(self, move, max_i): # 判斷下了棋之後 有哪些棋子要被翻轉
        global dh, dw
        h, w = self.move_to_location(move)

        if max_i==-1:
    
            for i in range(8):
                flip=False  #要不要翻
                k=1 #某方向走幾次
                if valid(h+dh[i]*k, w+dw[i]*k):
                    if (self.states[h+dh[i]*k][w+dw[i]*k]==mystate): #若某方向的第一個就是自己的，就算了
                        continue
                    while (self.states[h+dh[i]*k][w+dw[i]*k]!=0) : #某方向為敵隊(因為不為空，也不是自己)，就一直走下去直到找到自己
                        flip=True #若沒有遇到敵隊，隔壁就是空位，那也不能翻
                        k+=1
                        if not valid(h+dh[i], w+dw[i]): #某方向全是敵隊，就算了
                            continue 
                    if (self.states[h+dh[i]*k][w+dw[i]*k]==mystate) and (flip==True): #找到自己，而且剛剛有遇到敵隊
                        k-=1
                        while (self.states[h+dh[i]*k][w+dw[i]*k]!=mystate): #從最遠的敵隊翻回最新下的這個點
                            self.states[h+dh[i]*k][w+dw[i]*k]=mystate
                            k-=1
        else:
            flip=False  #要不要翻
            k=1 #某方向走幾次
            for i in range(8):
                if valid(h+dh[i]*k, w+dw[i]*k):
                    if (self.states[h+dh[i]*k][w+dw[i]*k]==mystate): #若某方向的第一個就是自己的，就算了
                        continue
                    while (self.states[h+dh[i]*k][w+dw[i]*k]!=0) : #某方向為敵隊(因為不為空，也不是自己)，就一直走下去直到找到自己
                        flip=True #若沒有遇到敵隊，隔壁就是空位，那也不能翻
                        k+=1
                        if not valid(h+dh[i], w+dw[i]): #某方向全是敵隊，就算了
                            continue 
                    if (self.states[h+dh[i]*k][w+dw[i]*k]==mystate) and (flip==True): #找到自己，而且剛剛有遇到敵隊
                        k-=1
                        while (self.states[h+dh[i]*k][w+dw[i]*k]!=mystate): #從最遠的敵隊翻回最新下的這個點
                            self.states[h+dh[i]*k][w+dw[i]*k]=mystate
                            k-=1


    def can_flip(self, move): # 判斷下了棋之後，最多能翻幾個，然後是哪個方向
        global dh, dw
        h, w = self.move_to_location(move)

        max_i=-1 #表可以翻最多的方向
        max_num=0 #表最多可翻幾個點
        for i in range(8):
            flip=False  #要不要翻
            k=1 #某方向走幾次
            if valid(h+dh[i]*k, w+dw[i]*k):
                if (self.states[h+dh[i]*k][w+dw[i]*k]==mystate): #若某方向的第一個就是自己的，就算了
                    continue
                while (self.states[h+dh[i]*k][w+dw[i]*k]!=0) : #某方向為敵隊(因為不為空，也不是自己)，就一直走下去直到找到自己
                    flip=True #若沒有遇到敵隊，隔壁就是空位，那也不能翻
                    k+=1
                    if not valid(h+dh[i], w+dw[i]): #某方向全是敵隊，就算了
                        continue 
                if (self.states[h+dh[i]*k][w+dw[i]*k]==mystate) and (flip==True): #找到自己，而且剛剛有遇到敵隊
                    if max_num<k-1:
                        max_num=k-1
                        max_i=i

        return max_num, max_i

    def get_available(self): #從空格找出可以下的步(可以翻對面的棋的步才可以走)
        max_flip=0
        max_point=-1
        for i in range(64):
            h, w = self.move_to_location(i)
            if self.states[h][w] != 0: # 這格已經有棋子了，就跳過
                continue

            max_num, max_i=self.can_flip(i)
            if max_num>max_flip:
                max_flip=max_num
                max_point=i
            if max_num>0 :
                self.availables.append(i) # 這格可以走，把他加入available
        if max_point==-1:
            return -1, -1
        h, w=self.move_to_location(max_point)
        return h, w
    def get_remain(self):
        for i in range(64):
            h, w = self.move_to_location(move)
            if self.states[h][w] != 0: # 這格已經有棋子了，就跳過
                continue
            self.remain.append(i) #沒有棋子，就加到remain


def GetStep(board, is_black):
    global mystate
    mystate=((is_black+1)%2)+1  # isblack=1 --> mystate=1   isblack=0 --> mystate=2
    
    board_class = Board(board, is_black)
    x, y=board_class.get_available()

    if x==-1:        
        x = random.randint(0, 7)
        y = random.randint(0, 7)
    return (x,y)
 
while(True):
    (stop_program, id_package, board, is_black) = STcpClient1.GetBoard()

    if(stop_program):
        break
    
    Step = GetStep(board, is_black)
    STcpClient1.SendStep(id_package, Step)
