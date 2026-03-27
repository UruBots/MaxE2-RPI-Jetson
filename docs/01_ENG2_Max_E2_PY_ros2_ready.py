from pycm import *
import time
import math
class CVar:
    IsTorqOn                = False
    nScreenWidth            = 0
    nScreenHeight           = 0
    IsResetCommand          = False
    nID                     = -1
    nOffset                 = 0
    nTouch_XY_X0            = 0
    nTouch_XY_Y0            = 0
    nTouch_Pos0             = 0
    nTouch_Pos_X0           = 0
    nTouch_Pos_Y0           = 0
    nTouch_XY_X1            = 0
    nTouch_XY_Y1            = 0
    nTouch_Pos1             = 0
    nTouch_Pos_X1           = 0
    nTouch_Pos_Y1           = 0
    nButton_0               = -1
    nButton_1               = -1
    nBack_Background        = 0
    btn0                    = None
    btn1                    = None
    nPage                   = -1
    nPage_Prev              = -1
    nSpeed                  = 0
    # For Face tracking
    IsTurning_Face          = True
    nPos_Servo              = 512
    m_nPwm                  = 0
    # For Walking
    nKnee                   = 0
    nWalking                = 0
    nWalking_Prev           = 0
class CTimer:
    nTimer                  = 0
    IsTimer                 = False
    def Set(self):
        self.IsTimer      = True
        self.nTimer       = millis()
    def Get(self):
        if self.IsTimer :
            return millis() - self.nTimer
        return 0
    def Destroy(self):
        self.IsTimer = False
_COLOR_NONE         = 0
_COLOR_WHITE        = 1
_COLOR_BLACK        = 2
_COLOR_RED          = 3
_COLOR_GREEN        = 4
_COLOR_BLUE         = 5
_COLOR_YELLOW       = 6
_COLOR_GRAY_LIGHT   = 7
_COLOR_GRAY         = 8
_COLOR_GRAY_DARK    = 9
_SHOW_IMAGE         = 0
_SHOW_TEXT          = 1
_SHOW_SHAPE         = 2
_SHOW_NUM           = 3
_RATIO              = 1000
_BTN_INDEX          = 4

#1..5
#[left,top,right,bottom, 고유 번호(ButtonNumber)] : left, top < 0 then 1..5 position
# (English) [left,top,right,bottom, ButtonNumber] : left, top < 0 then 1..5 position
# 각 버튼의 좌표와 넣고싶은 고유 번호를 여기서 넣고 - step 1/2 [주의 : 고유번호(ButtonNumber)는 다른 버튼과 겹치지 않도록 한다.]
# (English) Add the each button's coordinates - step 1/2. Be sure not to overlap ButtonNumber with the other buttons.

_BTN_MENU           = [20,40,160,150,1]
_BTN_REMOTE_NORMAL  = [460,30,520,150,2]
_BTN_REMOTE_FIGHT   = [660,30,716,150,3]
_BTN_REMOTE_SPECIAL = [846,30,900,150,5]

#Menu-Control
_BTN_SUB_OUT        = [1,1,1000,700,60]
_BTN_SUB_X          = [950,730,990,780,61]
_BTN_SUB_REMOTE     = [100-50,850-100,100+50,850+100,62]
_BTN_SUB_STREAM     = [250-50,850-100,250+50,850+100,64]
_BTN_SUB_FACE_TRACK = [400-50,850-100,400+50,850+100,64]
_BTN_SUB_MOTOR      = [700-50,850-100,700+50,850+100,65]
_BTN_SUB_OFFSET     = [850-50,850-100,850+50,850+100,66]

#회전 버튼
# (English) Button for turn.
_BTN_TURN_L         = [20,220,130,330,6]
_BTN_TURN_R         = [240,220,350,330,7]

#-대-Diagonal
# (English) Button for diagonal
_BTN_MOVE_DG_FL     = [40,370,100,490,8]
_BTN_MOVE_DG_FR     = [260,370,330,490,9]
_BTN_MOVE_DG_BL     = [40,840,100,930,10]
_BTN_MOVE_DG_BR     = [260,840,330,930,11]

#이동 버튼
# (English) Button for walking.
_BTN_MOVE_UL        = [90,500,140,570,12]
_BTN_MOVE_U         = [160,420,210,540,13]
_BTN_MOVE_UR        = [220,500,280,570,14]
_BTN_MOVE_L         = [60,580,120,700,15]
_BTN_MOVE_R         = [240,580,310,700,16]
_BTN_MOVE_DL        = [90,730,140,810,17]
_BTN_MOVE_D         = [160,760,210,880,18]
_BTN_MOVE_DR        = [220,730,280,810,19]

#모션 속도 버튼
# (English) Button for motion speed
_BTN_SPD            = [140,590,220,720,20]

#토크 ON/OFF 버튼
# (English) Button for Torque ON/OFF
_BTN_TORQ           = [440,520,570,630,21]

#LED 변경 버튼
# (English) Button for LED.
_BTN_LED            = [440,660,570,770,22]

#일어나기 버튼
# (English) Button for standup
_BTN_GETUP          = [440,790,570,900,23]

#노멀 모드 액션 버튼
# (English) Button for action in Normal mode.
_BTN_ACT_01         = [630,280,750,380,30] #손인사 # (English) Shaking hands
_BTN_ACT_02         = [820,280,940,380,31] #굽혀인사 # (English) Take a bow
_BTN_ACT_03         = [630,450,750,550,32] #세레모니 # (English) Ceremony
_BTN_ACT_04         = [820,450,940,550,33] #도발 # (English) Provoke
_BTN_ACT_05         = [630,630,750,730,34] #물구나무 # (English) Handstand
_BTN_ACT_06         = [820,630,940,730,35] #팔굽혀펴기 # (English) Pushup
_BTN_ACT_07         = [630,790,750,890,36] #박수 # (English) Clap
_BTN_ACT_08         = [820,790,940,890,37] #옆구르기 Rolling Rolling 

#격투 모드 액션 버튼
# (English) Button for action in Fight mode.
_BTN_ACT_09         = [760,280,810,390,38]
_BTN_ACT_10         = [760,450,810,560,39]

# Motor ID Tag
_MOT_W = 80
_MOT_H = 50

_BTN_ID_01 = [350-_MOT_W,80-_MOT_H,350+_MOT_W,  80+_MOT_H,101]
_BTN_ID_02 = [300-_MOT_W,200-_MOT_H,300+_MOT_W,200+_MOT_H,102]
_BTN_ID_03 = [650-_MOT_W,80-_MOT_H,650+_MOT_W,  80+_MOT_H,103]
_BTN_ID_04 = [700-_MOT_W,200-_MOT_H,700+_MOT_W,200+_MOT_H,104]
_BTN_ID_05 = [400-_MOT_W,420-_MOT_H,400+_MOT_W,420+_MOT_H,105]
_BTN_ID_06 = [400-_MOT_W,540-_MOT_H,400+_MOT_W,540+_MOT_H,106]
_BTN_ID_07 = [600-_MOT_W,420-_MOT_H,600+_MOT_W,420+_MOT_H,107]
_BTN_ID_08 = [600-_MOT_W,540-_MOT_H,600+_MOT_W,540+_MOT_H,108]
_BTN_ID_09 = [400-_MOT_W,780-_MOT_H,400+_MOT_W,780+_MOT_H,109]
_BTN_ID_10 = [400-_MOT_W,900-_MOT_H,400+_MOT_W,900+_MOT_H,110]
_BTN_ID_11 = [600-_MOT_W,780-_MOT_H,600+_MOT_W,780+_MOT_H,111]
_BTN_ID_12 = [600-_MOT_W,900-_MOT_H,600+_MOT_W,900+_MOT_H,112]
_BTN_ID_13 = [250-_MOT_W,320-_MOT_H,250+_MOT_W,320+_MOT_H,113]
_BTN_ID_14 = [750-_MOT_W,320-_MOT_H,750+_MOT_W,320+_MOT_H,114]
_BTN_ID_15 = [400-_MOT_W,660-_MOT_H,400+_MOT_W,660+_MOT_H,115]
_BTN_ID_16 = [600-_MOT_W,660-_MOT_H,600+_MOT_W,660+_MOT_H,116]
_BTN_ID_17 = [500-_MOT_W,300-_MOT_H,500+_MOT_W,300+_MOT_H,117]

# Reset & Init ( Offset )
_BTN_RESET = [900-70,300-250,900+70,300,82]
_BTN_INIT = [900-70,300,900+70,300+250,83]

#오프셋 설정 대화상자
# (English) Dialog of Offset setting.
_BTN_DIALOG_OK      = [600-100,800-80,600+100,800+80,84]
_BTN_DIALOG_CANCEL  = [400-100,800-80,400+100,800+80,85]
_BTN_DIALOG_TORQ    = [600- 80,400-50,600+ 80,400+50,86]
_BTN_DIALOG_PLUS    = [640- 50,560-50,640+ 50,560+50,87]
_BTN_DIALOG_MINUS   = [360- 50,560-50,360+ 50,560+50,88]
_PAGE_MENU                  = 0
_PAGE_REMOTE_NORMAL         = 1
_PAGE_REMOTE_FIGHT          = 2
_PAGE_REMOTE_SPECIAL        = 5
_PAGE_STREAM                = 6
_PAGE_FACE_TRACK            = 7
_PAGE_MOTOR_TEST            = 8
_PAGE_OFFSET                = 9
_PAGE_OFFSET_DIALOG1        = 10
_PAGE_OFFSET_DIALOG2        = 11
_PAGE_OFFSET_DIALOG_CLOSE   = 12

#모션에서 동작하는게 아닌 일반적인 동작상에서의 오프셋 적용 
# (English) Set Offest value in general movement (Not in the Motion).
#           0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17   18 19 20

aOffset = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
btnList             = None
tmrTorqBtn          = CTimer()
IsPhone             = False
def ShowPage(nPage):
    global btnList
    CVar.nPage_Prev = CVar.nPage
    CVar.nPage = nPage
    # 여기서 페이지를 만들어 해당 버튼을 할당받는다. - step 2/2
    # (English) Assign the button by creating the page. - step 2/2 
    if nPage == _PAGE_MENU:
        btnList = [
            _BTN_SUB_OUT,
            _BTN_SUB_X,
            _BTN_SUB_REMOTE,
            _BTN_SUB_STREAM,
            _BTN_SUB_FACE_TRACK,
            _BTN_SUB_MOTOR,
            _BTN_SUB_OFFSET
            ]
        
        # 0:닫기, 1:색상, 2:얼굴감지, 3:스트리밍, 4:마커, 5:레인, 6:감정, 7:손 # (English) rpi.mode(0)
        # (English) 0: Close, 1:Color, 2: Facial Detection, 3:Streaming, 4: Marker, 5: Lane, 6: Emotion, 7: Hands
        rpi.mode(0) 
        
        #스마트폰 스트리밍 영상화면 0:닫기, 1:표시 
        # (English) Smart device's video streaming 0: Close, 1: Display
        smart.write8(10700, 0)
        Show_Image(500, 850, 1)
        
        #_BTN_SUB_OUT 을 제외한 다른 버튼들은 이미지가 있다.
        # (English) Note that buttons have their own images aside from _BTN_SUB_OUT, 
        img = [2,3,4,6,7,8]
        nIndex = 0
        for btn in btnList :
            if (btn != _BTN_SUB_OUT):
                Show_Image(
                    round((btn[0] + btn[2]) / 2),
                    round((btn[1] + btn[3]) / 2),
                    img[nIndex]
                )
                nIndex = nIndex + 1
        
        #Setup_Speed(254, 0)
        # 전체모터 토크 On
        # (English) Torque On for all DYNAMIXELs
        TorqAll(True)
        
        #모든 LED Off(65번지에 8바이트 명령을 직접 보냄)
        # (English) Light off all LED (8 bytes data will be transmitted to the address 65)        
        DXL(254).write8(65, 0)
        Motion_Ready(1)
        
        #머리를 가운데로...
        # (English) Align the head center.        
        OLLO(1, const.OLLO_JOINT_POSITION).write(512)
        Clear_Text()
    elif nPage == _PAGE_REMOTE_NORMAL:
        Clear_All()
        btnList = [
            _BTN_MENU,
            _BTN_REMOTE_NORMAL,
            _BTN_REMOTE_FIGHT,
            _BTN_REMOTE_SPECIAL,
            
            #회전 버튼
            # (English) Button for turn.            
            _BTN_TURN_L,
            _BTN_TURN_R,
            #-대각-Diagonal
            # (English) Button for diagonal            
            _BTN_MOVE_DG_FL,
            _BTN_MOVE_DG_FR,
            _BTN_MOVE_DG_BL,
            _BTN_MOVE_DG_BR,
            #이동 버튼
            # (English) Button for walking.            
            _BTN_MOVE_UL,
            _BTN_MOVE_U,
            _BTN_MOVE_UR,
            _BTN_MOVE_L,
            _BTN_MOVE_R,
            _BTN_MOVE_DL,
            _BTN_MOVE_D,
            _BTN_MOVE_DR,
            _BTN_MOVE_DR,
            #토크 ON/OFF 버튼
            # (English) Button for Torque ON/OFF            
            _BTN_SPD,
            _BTN_TORQ,
            #LED 변경 버튼
            # (English) Button for LED.            
            _BTN_LED,
            #일어나기 버튼
            # (English) Button for standup            
            _BTN_GETUP,
            #노멀 모드 액션 버튼
            # (English) Button for action in Normal mode.            
            _BTN_ACT_02, #손인사 (English) Shaking hands
            _BTN_ACT_01, #굽혀인사 (English) Take a bow 
            _BTN_ACT_03, #세레모니 (English) Ceremony
            _BTN_ACT_04, #도발 (English) Provoke
            _BTN_ACT_05, #물구나무 (English) Handstand
            _BTN_ACT_06, #팔굽혀펴기 (English) Pushup
            _BTN_ACT_07, #박수 (English) Clap
            _BTN_ACT_08  #옆구르기 (English) Rolling Rolling 
            ]
        Show_Background(1 + CVar.nSpeed)
        Motion_Ready(1)
        nMotion_Prev = 0
    elif nPage == _PAGE_REMOTE_FIGHT:
        Clear_All()
        btnList = [
            _BTN_MENU,
            _BTN_REMOTE_NORMAL,
            _BTN_REMOTE_FIGHT,
            _BTN_REMOTE_SPECIAL,
            #회전 버튼
            # (English) Button for turn.            
            _BTN_TURN_L,
            _BTN_TURN_R,
            
            #-대각-Diagonal
            # (English) Button for diagonal            
            _BTN_MOVE_DG_FL,
            _BTN_MOVE_DG_FR,
            _BTN_MOVE_DG_BL,
            _BTN_MOVE_DG_BR,
            #이동 버튼
            # (English) Button for walking.            
            _BTN_MOVE_UL,
            _BTN_MOVE_U,
            _BTN_MOVE_UR,
            _BTN_MOVE_L,
            _BTN_MOVE_R,
            _BTN_MOVE_DL,
            _BTN_MOVE_D,
            _BTN_MOVE_DR,
            _BTN_MOVE_DR,
            #모션 속도 버튼
            # (English) Button for motion speed            
            _BTN_SPD,
            #토크 ON/OFF 버튼
            # (English) Button for Torque ON/OFF            
            _BTN_TORQ,
            #LED 변경 버튼
            # (English) Button for LED.            
            _BTN_LED,
            #일어나기 버튼
            # (English) Button for standup            
            _BTN_GETUP,
            #노멀 모드 액션 버튼
            # (English) Button for action in Normal mode.            
            _BTN_ACT_01, #좌전방 # (English) Left forward
            _BTN_ACT_02, #우전방 # (English) Right forward
            _BTN_ACT_03, #좌전방 허리 스트레이트 # (English) Left straight
            _BTN_ACT_04, #우전방 허리 스트레이트 # (English) Right straight
            _BTN_ACT_05, #좌 사이드 # (English) Left side
            _BTN_ACT_06, #우 사이드 # (English) Right side
            _BTN_ACT_07, #좌회전 펀치  # (English) Left punch
            _BTN_ACT_08, #우회전 펀치 # (English) Right punch
            _BTN_ACT_09, #몸던지기 # (English) Body throw.
            _BTN_ACT_10, #방어 # (English) Guard
            ]
        Show_Background(3 + CVar.nSpeed)
        Motion_Ready(2)
        nMotion_Prev = 0
    elif nPage == _PAGE_REMOTE_SPECIAL:
        Clear_All()
        btnList = [
            _BTN_MENU,
            _BTN_REMOTE_NORMAL,
            _BTN_REMOTE_FIGHT,
            _BTN_REMOTE_SPECIAL,
            #회전 버튼
            # (English) Button for turn.            
            _BTN_TURN_L,
            _BTN_TURN_R,
            _BTN_MOVE_UL,
            _BTN_MOVE_U,
            _BTN_MOVE_UR,
            _BTN_MOVE_L,
            _BTN_MOVE_R,
            _BTN_MOVE_DL,
            _BTN_MOVE_D,
            _BTN_MOVE_DR,
            _BTN_MOVE_DR,
            #모션 속도 버튼
            # (English) Button for motion speed            
            _BTN_SPD,
            #토크 ON/OFF 버튼
            # (English) Button for Torque ON/OFF            
            _BTN_TORQ,
            #LED 변경 버튼
            # (English) Button for LED.            
            _BTN_LED,
            #일어나기 버튼
            # (English) Button for standup            
            _BTN_GETUP,
            
            #노멀 모드 액션 버튼
            # (English) Button for action in Normal mode.            
            _BTN_ACT_01,
            _BTN_ACT_02,
            _BTN_ACT_03,
            _BTN_ACT_04,
            _BTN_ACT_05,
            _BTN_ACT_06,
            _BTN_ACT_07,
            _BTN_ACT_08
            ]
        Show_Background(5)
        Motion_Ready(1)
        nMotion_Prev = 0
    elif nPage == _PAGE_STREAM:
        Clear_All()
        btnList = [
            _BTN_MENU,
            #회전 버튼
            # (English) Button for turn.            
            _BTN_TURN_L,
            _BTN_TURN_R,
            #-대각-Diagonal
            # (English) Button for diagonal            
            _BTN_MOVE_DG_FL,
            _BTN_MOVE_DG_FR,
            _BTN_MOVE_DG_BL,
            _BTN_MOVE_DG_BR,
            #이동 버튼
            # (English) Button for walking.            
            _BTN_MOVE_UL,
            _BTN_MOVE_U,
            _BTN_MOVE_UR,
            _BTN_MOVE_L,
            _BTN_MOVE_R,
            _BTN_MOVE_DL,
            _BTN_MOVE_D,
            _BTN_MOVE_DR,
            _BTN_MOVE_DR,
            #모션 속도 버튼
            # (English) Button for motion speed            
            _BTN_SPD,
            #토크 ON/OFF 버튼
            # (English) Button for Torque ON/OFF            
            _BTN_TORQ,
            #LED 변경 버튼
            # (English) Button for LED.            
            _BTN_LED,
            #일어나기 버튼
            # (English) Button for standup            
            _BTN_GETUP,
            #노멀 모드 액션 버튼
            # (English) Button for action in Normal mode.            
            _BTN_ACT_01, #손인사 
            _BTN_ACT_02, #굽혀인사 # (English) Take a bow 
            _BTN_ACT_03, #세레모니 # (English) Ceremony 
            _BTN_ACT_04, #도발 # (English) Provoke 
            _BTN_ACT_05, #물구나무 # (English) Handstand 
            _BTN_ACT_06, #팔굽혀펴기 # (English) Pushup 
            _BTN_ACT_07, #박수 # (English) Clap 
            _BTN_ACT_08 #옆구르기 # (English) Rolling Rolling 
            ]
        Show_Background(11 + CVar.nSpeed)
        # 0:닫기, 1:색상, 2:얼굴감지, 3:스트리밍, 4:마커, 5:레인, 6:감정, 7:손 
        # (English) 0: Close, 1:Color, 2: Facial Detection, 3:Streaming, 4: Marker, 5: Lane, 6: Emotion, 7: Hands
        rpi.mode(3)
        smart.write8(10700, 1)
        # 다리를 벌린자세이므로 이걸 2로 해야 Motion_Ready()에서 다리를 모으는 동작을 한다 
        # (English) As this the straddle position, set this number as 2 to make the legs straddle with Motion_Ready().
        Motion_Ready(2)
        nMotion_Prev = 0
    elif nPage == _PAGE_FACE_TRACK:
        Clear_All()
        btnList = [
            _BTN_MENU
            ]
        Show_Background(13)
        CVar.nPos_Servo = 512
        Motion_Ready(2)
        Motion_Play(13)
        OLLO(1, const.OLLO_JOINT_POSITION).write(CVar.nPos_Servo)
        # 0:닫기, 1:색상, 2:얼굴감지, 3:스트리밍, 4:마커, 5:레인, 6:감정, 7:손
        # (English) 0: Close, 1:Color, 2: Facial Detection, 3:Streaming, 4: Marker, 5: Lane, 6: Emotion, 7: Hands        
        rpi.mode(2)
        smart.write8(10700, 0)
    elif nPage == _PAGE_MOTOR_TEST:
        Clear_All()
        btnList = [
            _BTN_MENU,
            _BTN_ID_01,
            _BTN_ID_02,
            _BTN_ID_03,
            _BTN_ID_04,
            _BTN_ID_05,
            _BTN_ID_06,
            _BTN_ID_07,
            _BTN_ID_08,
            _BTN_ID_09,
            _BTN_ID_10,
            _BTN_ID_11,
            _BTN_ID_12,
            _BTN_ID_13,
            _BTN_ID_14,
            _BTN_ID_15,
            _BTN_ID_16,
            _BTN_ID_17
            ]
            
        # 초기자세(무릎세운자세)
        # (English) Init pose (Knee up posture)
        Show_Background(14)
        Show_Motors(-1)
        Motion_Play_And_Wait(15)
        Move_Center(True)
        #모든 LED Off
        # (English) Light off all LED.        
        DXL(254).write8(65, 0)
        # Off
        Led(-1)
    elif nPage == _PAGE_OFFSET:
        Clear_All()
        btnList = [
            _BTN_MENU,
            _BTN_ID_01,
            _BTN_ID_02,
            _BTN_ID_03,
            _BTN_ID_04,
            _BTN_ID_05,
            _BTN_ID_06,
            _BTN_ID_07,
            _BTN_ID_08,
            _BTN_ID_09,
            _BTN_ID_10,
            _BTN_ID_11,
            _BTN_ID_12,
            _BTN_ID_13,
            _BTN_ID_14,
            _BTN_ID_15,
            _BTN_ID_16,
            _BTN_ID_17,
            _BTN_RESET,
            _BTN_INIT
            ]
        Show_Background(14)
        Show_Motors(-1)
        # Reset & Init Pos        
        Show_Image(900, 300, 9)
        Motion_Play_And_Wait(15)
        # 모든 모터 가운데 정렬
        # (English) Align center all DYNAMIXEL.        
        Move_Center(True)
        Led(-1)
    elif nPage == _PAGE_OFFSET_DIALOG1:
        btnList = [
            _BTN_DIALOG_OK,
            _BTN_DIALOG_CANCEL,
            _BTN_DIALOG_TORQ,
            _BTN_DIALOG_PLUS,
            _BTN_DIALOG_MINUS
            ]
        # Clear - 대화상자 배경
        # (English) Clear - Background image of the dialog box.        
        Show_Dialog(1, CVar.nID)
    elif nPage == _PAGE_OFFSET_DIALOG2:
        btnList = [
            _BTN_DIALOG_OK,
            _BTN_DIALOG_CANCEL
            ]
        Show_Dialog(2, CVar.nID)
    elif nPage == _PAGE_OFFSET_DIALOG_CLOSE:
        btnList = [
            _BTN_MENU,
            _BTN_ID_01,
            _BTN_ID_02,
            _BTN_ID_03,
            _BTN_ID_04,
            _BTN_ID_05,
            _BTN_ID_06,
            _BTN_ID_07,
            _BTN_ID_08,
            _BTN_ID_09,
            _BTN_ID_10,
            _BTN_ID_11,
            _BTN_ID_12,
            _BTN_ID_13,
            _BTN_ID_14,
            _BTN_ID_15,
            _BTN_ID_16,
            _BTN_ID_17,
            _BTN_RESET,
            _BTN_INIT
            ]
        Show_Dialog(0)
    else :
        btnList = [
            _BTN_MENU
            ]
def Show_Motors(nSelect):
    #[off]11,12,13,... <-> [on]31,32,33,...
    for i in range(0, 17):
        nAdd = 0
        # 선택된 모터는 [On]이 표시
        # (English) Mark [On] for the selected DYNAMIXEL.
        if nSelect == i + 1:
            nAdd = nAdd + 20
        Show_Image(round((btnList[i+1][0] + btnList[i+1][2]) / 2),round((btnList[i+1][1] + btnList[i+1][3]) / 2), i + 11 + nAdd)
def GetUp() :
    if (CVar.IsTorqOn == False):
        # 전체모터 토크 On
        # (English) Torque On for all DYNAMIXELs        
        TorqAll(True)
    nStandup = 0
    if (CVar.nPage != _PAGE_REMOTE_FIGHT) and (CVar.nPage != _PAGE_STREAM):
        nStandup = 100
    if (imu.pitch() > 6000) : #앞으로 넘어짐 # (English) Fall front
        Motion_Play_And_Wait(3)
        nStandup += 2
    elif (imu.pitch() < -6000) : #뒤로 넘어짐 # (English) Fall backward
        Motion_Play_And_Wait(4)
        nStandup += 2
    if (nStandup > 100):
        Motion_Play_And_Wait(16)
    elif (nStandup == 100):
        Motion_Play_And_Wait(1)
    else :
        Motion_Play_And_Wait(2)
nMotion_Ready = -1
def Motion_Ready(nInit = 2):
    global nMotion_Ready
    # 전체모터 토크 On
    # (English) Torque On for all DYNAMIXELs    
    TorqAll(True)
    # 모터 전체 위치 업데이트
    # (English) Update the all DYNAMIXEL's position.    
    PositionUpdate()
    if (nInit == 2) :
        Motion_Play_And_Wait(2)
    else :
        if (nMotion_Ready < 0):
            Motion_Play_And_Wait(2)
            Motion_Play_And_Wait(16)
        else:
            if (nInit != nMotion_Ready):
                if (nInit != 2) :
                    Motion_Play_And_Wait(16)
        Motion_Play_And_Wait(1)
    nMotion_Ready = nInit
def Motion_Stop():
    Motion_Play(-3)
nMotion_Prev = 0
def Motion_Play(nMotionIndex, nNextMotion = 0):
    global nMotion_Prev
    if (nMotionIndex <= 0):
    # 정지동작 (0)
    # (English) Stop (0)
    # nMotionIndex => -3:바로 종료, -2:step(Key-Frame) 실행 후 종료, -1:page(motion Unit) 실행후 종료, 0: page(motion Unit) 실행후 exit 실행후 종료.
    # (English) nMotionIndex => -3:Prompt termination, -2:step(Key-Frame) Termination after execution, -1:page(motion Unit) Termination after execution, 0: page(motion Unit) Termination after excution of exit        
	    motion.play((int)(nMotionIndex))
    else:
        Setup_Speed(254, 0)
        if (nNextMotion == 0) :
            motion.play((int)(nMotionIndex))
        else :
            motion.play((int)(nMotionIndex), (int)(nNextMotion))
    nMotion_Prev = nMotionIndex
def Motion_Play_And_Wait(nMotionIndex, nNextMotion = 0):
    Motion_Play(nMotionIndex, nNextMotion)
    Motion_Wait()
def Motion_Wait() :
    while motion.status():
        if btnList != None:
            # 버튼 눌림 체크 - 터치의 소비
            # (English) Checking the button push            
            nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1 = GetButton(btnList)
def TorqAll(IsOn, IsSound = None):
    TorqOnOff(-1, IsOn, IsSound)
def TorqOnOff(nNum, IsOn, IsSound = None):
    global nMotion_Ready
    if (IsOn == True) :
        if IsSound == True :
            buzzer.melody(14)
        if (nNum >= 0) :
            DXL(nNum).torque_on()
        else :
            dxlbus.torque_on()
            CVar.IsTorqOn = True
    else :
        nMotion_Ready = -1
        CVar.IsTorqOn = False
        if IsSound == True :
            buzzer.melody(15)
        if (nNum >= 0) :
            DXL(nNum).torque_off()
        else :
            dxlbus.torque_off()
def GetResolution():
    for i in range(0, 100):
        screen = smart.read32(10460)
        CVar.nScreenWidth = screen & 0x0000FFFF
        CVar.nScreenHeight = (screen & 0xFFFF0000) >> 16
        if CVar.nScreenWidth > 0 and CVar.nScreenWidth < 65535 and CVar.nScreenHeight > 0 and CVar.nScreenHeight < 65535:
            break
def GetTouch_Down():
    #  1  2  3  4  5
    #  6  7  8  9 10
    # 11 12 13 14 15
    # 16 17 18 19 20
    # 21 22 23 24 25    
    if (smart.is_connected() == True):
        XY_X0 = 0
        XY_Y0 = 0
        Pos_X0 = 0
        Pos_Y0 = 0
        Pos0 = 0
        XY_X1 = 0
        XY_Y1 = 0
        Pos_X1 = 0
        Pos_Y1 = 0
        Pos1 = 0
        # Touch - First            
        Tmp = smart.read64(10470) # 터치입력좌표 # (English) Coordinates for touch input.
        nTouch0 = Tmp[0] & 0xffffffff
        nTouch1 = Tmp[1] & 0xffffffff
        IsChanged = False
        if (nTouch0 > 0) :
            XY_X0 = nTouch0 & 0x0000FFFF
            XY_Y0 = (nTouch0 >> 16) & 0x0000FFFF
            Pos_X0 = (int)((XY_X0 / CVar.nScreenWidth) * 5 + 1)
            Pos_Y0 = (int)((XY_Y0 / CVar.nScreenHeight) * 5 + 1)
            Pos0 = Pos_X0 + (Pos_Y0 - 1) * 5
            XY_X0 = (int)(XY_X0 * _RATIO / CVar.nScreenWidth)
            XY_Y0 = (int)(XY_Y0 * _RATIO / CVar.nScreenHeight)
            if (nTouch1 > 0) :
                XY_X1 = nTouch1 & 0x0000FFFF
                XY_Y1 = (nTouch1 >> 16) & 0x0000FFFF
                Pos_X1 = (int)((XY_X1 / CVar.nScreenWidth) * 5 + 1)
                Pos_Y1 = (int)((XY_Y1 / CVar.nScreenHeight) * 5 + 1)
                Pos1 = Pos_X1 + (Pos_Y1 - 1) * 5
                XY_X1 = (int)(XY_X1 * _RATIO / CVar.nScreenWidth)
                XY_Y1 = (int)(XY_Y1 * _RATIO / CVar.nScreenHeight)
            CVar.nTouch_Pos0 = Pos0
            CVar.nTouch_Pos_X0 = Pos_X0
            CVar.nTouch_Pos_Y0 = Pos_Y0
            CVar.nTouch_XY_X0 = XY_X0
            CVar.nTouch_XY_Y0 = XY_Y0
            CVar.nTouch_Pos1 = Pos1
            CVar.nTouch_Pos_X1 = Pos_X1
            CVar.nTouch_Pos_Y1 = Pos_Y1
            CVar.nTouch_XY_X1 = XY_X1
            CVar.nTouch_XY_Y1 = XY_Y1
        else :
            CVar.nTouch_Pos0 = 0
            CVar.nTouch_Pos_X0 = 0
            CVar.nTouch_Pos_Y0 = 0
            CVar.nTouch_XY_X0 = 0
            CVar.nTouch_XY_Y0 = 0
            CVar.nTouch_Pos1 = 0
            CVar.nTouch_Pos_X1 = 0
            CVar.nTouch_Pos_Y1 = 0
            CVar.nTouch_XY_X1 = 0
            CVar.nTouch_XY_Y1 = 0
    else :
        IsPhone = False
# 1~100 사이의 좌표값을 입력하면 스마트폰에 맞는 좌표값으로 변환
# (English) Convert the value matching to the value of the smart device in use if the range of coordinate's value from 1 to 100. 
def Set(nX, nY):
    nResX = nX * CVar.nScreenWidth / _RATIO
    nResY = nY * CVar.nScreenHeight / _RATIO
    return nResX, nResY
def IsButton(nX, nY, Btn):
    if (Btn[0] < 0):
        right = (Btn[0] * -200)
        left = right - 200
        bottom = (Btn[1] * -200)
        top = bottom - 200
        if ((nY >= top) and (nY <= bottom)):
            if ((nX >= left) and (nX <= right)):
                return True
    else:
        if ((nY >= Btn[1]) and (nY <= Btn[3])):
            if ((nX >= Btn[0]) and (nX <= Btn[2])):
                return True
    return False

# 모터전체 위치업데이트
# (English) Update all DYNAMIXEL position. 
def PositionUpdate():
    etc.write8(65,3)
    while(True) :
        if etc.read8(65) == 0 :
            break

#출력숫자 간단 테스트
# (English) Brief number printing test 
def Show_Num(nX, nY, nValue, nColor = _COLOR_NONE, nSize = None):
    if (nSize == 0):
        Clear_Num(nX, nY)
    elif (nColor == _COLOR_NONE):
        Show(_SHOW_NUM, nX, nY, 60, _COLOR_RED, nValue)
    elif (nSize == None):
        Show(_SHOW_NUM, nX, nY, 60, nColor, nValue)
    else:
        Show(_SHOW_NUM, nX, nY, nSize, nColor, nValue)
def Show_Point(nX, nY, nColor, nSize = None):
    if (nSize == None):
        Show(_SHOW_SHAPE, nX, nY, 20, nColor, 1)
    else:
        Show(_SHOW_SHAPE, nX, nY, nSize, nColor, 1)
def Show_Text(nX, nY, nValue, nColor = _COLOR_NONE, nSize = None):
    if (nColor == _COLOR_NONE):
        Show(_SHOW_TEXT, nX, nY, 60, _COLOR_RED, nValue)
    elif (nSize == None):
        Show(_SHOW_TEXT, nX, nY, 60, nColor, nValue)
    else:
        Show(_SHOW_TEXT, nX, nY, nSize, nColor, nValue)
def Show_Image(nX, nY, nValue, nSize = None):
    if (nSize == None):
        Show(_SHOW_IMAGE, nX, nY, 1, 0, nValue)
    else:
        Show(_SHOW_SHAPE, nX, nY, nSize, 0, nValue)
def Show_Background(nValue):
    if (nValue != CVar.nBack_Background):
        smart.display.back_image(nValue)
        CVar.nBack_Background = nValue

# nShowType : 0 - 그림, 1 - 문자, 2 - 도형, 3 - 숫자
# (English) nShowType : 0 - Image, 1 - Letter, 2 - Diagram, 3 - Number
# nValue ([Image - Index], [Shape - 1:원, 2:사각, 3:삼각], [Text - Index], [Num - Value])
# (English) nValue ([Image - Index], [Shape - 1: Circle, 2:Retencgular, 3:Triangle], [Text - Index], [Num - Value])
# nColor (0:알 수 없음, 1:흰색, 2:검은색, 3:빨간색, 4:녹색, 5:청색 6:노랑색, 7:옅은회색, 8:회색, 9:어두운 회색)
# (English) nColor (0:Unknown, 1:White, 2:Black, 3:Red, 4:Green, 5:Blue 6:Yellow, 7:Light grey, 8:Grey, 9:Deep grey)

def Show(nShowType, nX, nY, nSize, nColor, nValue):
    if ((nShowType >= 0) and (nShowType < 4)):
        nX, nY = Set(nX, nY)
        smart.write32(10480, int(nX) | (int(nY) << 16))
        nTmp = nValue * 256 + nSize * 65536 + nColor * 16777216
        if (nShowType == _SHOW_IMAGE) : # 0xff000000 자리의 color 값 사용 안함
            smart.display.front_image(nTmp & 16777215) # & 0xffffff(=16777215)
        elif (nShowType == _SHOW_SHAPE) :
            smart.display.shape(nTmp)
        elif (nShowType == _SHOW_TEXT) :
            smart.display.text(nTmp)
        elif (nShowType == _SHOW_NUM) :
            smart.display.number(nTmp)
def Clear_All():
    smart.write32(10480, 0)
    smart.display.front_image(0)
    smart.display.shape(0)
    smart.display.text(0)
    smart.display.number(0)
def Clear_Shape():
    smart.write32(10480, 0)
    smart.display.shape(0)
def Clear_Text():
    smart.write32(10480, 0)
    smart.display.text(0)
def Clear_Num(nX = None, nY = None):
    if (nX == None) or (nY == None) :
        smart.write32(10480, 0)
        smart.display.number(0)
    else :
        Show(_SHOW_NUM, nX, nY, 0, 0, 0)
# [nRed: 0~100], [nBlue: 0~100]
def LedPwm(nRed, nBlue):
    OLLO(2, const.OLLO_RED_BRIGHTNESS).write(round(nRed)) # 0~100
    OLLO(2, const.OLLO_BLUE_BRIGHTNESS).write(round(nBlue)) # 0~100
def Led(nValue = 0):
    red_led = OLLO(2, const.OLLO_RED_BRIGHTNESS)
    blue_led = OLLO(2, const.OLLO_BLUE_BRIGHTNESS)
    nRed = 0
    nBlue = 0
    if nValue == 0:
        if red_led.read() > 0 and blue_led.read() > 0:
            pass
        elif red_led.read() <= 0 and blue_led.read() <= 0:
            nRed = 100
        elif red_led.read() > 0 and blue_led.read() <= 0:
            nBlue = 100
        else:
            nRed = 100
            nBlue = 100
        red_led.write(nRed) # 0~100
        blue_led.write(nBlue) # 0~100
    elif nValue < 0:
        red_led.write(0) # 0~100
        blue_led.write(0) # 0~100
    # manual change
    else :
        red_led.write(100 * (nValue % 2)) # 0~100
        blue_led.write(int(nValue / 2)) # 0~100

# ROS 2 / Remocon bridge protocol via rc.read()
# 10000 + motion_page => execute motion.play(page)
# 20000..20003        => LED presets
# 30000 + head_raw    => OLLO head raw position (0..1023)
ROS_MOTION_BASE = 10000
ROS_MOTION_MAX = 10999
ROS_LED_OFF = 20000
ROS_LED_RED = 20001
ROS_LED_BLUE = 20002
ROS_LED_MAGENTA = 20003
ROS_HEAD_BASE = 30000
ROS_HEAD_MIN = ROS_HEAD_BASE
ROS_HEAD_MAX = ROS_HEAD_BASE + 1023
ROS_HEAD_CLAMP_MIN = 280
ROS_HEAD_CLAMP_MAX = 760

def Clamp(nValue, nMin, nMax):
    if nValue < nMin:
        return nMin
    if nValue > nMax:
        return nMax
    return nValue

def HandleRosRemocon():
    if rc.received() != True:
        return False

    nValue = int(rc.read())
    IsHandled = False

    # Motion pages sent by ROS 2 through cm550_remocon_bridge_node.
    if (nValue >= ROS_MOTION_BASE) and (nValue <= ROS_MOTION_MAX):
        Motion_Play(int(nValue - ROS_MOTION_BASE))
        IsHandled = True
    # Head raw command sent by cm550_remocon_bridge_node.
    elif (nValue >= ROS_HEAD_MIN) and (nValue <= ROS_HEAD_MAX):
        nHead = Clamp(int(nValue - ROS_HEAD_BASE), ROS_HEAD_CLAMP_MIN, ROS_HEAD_CLAMP_MAX)
        CVar.nPos_Servo = nHead
        OLLO(1, const.OLLO_JOINT_POSITION).write(nHead)
        IsHandled = True
    # LED presets sent by cm550_remocon_bridge_node.
    elif nValue == ROS_LED_OFF:
        LedPwm(0, 0)
        IsHandled = True
    elif nValue == ROS_LED_RED:
        LedPwm(100, 0)
        IsHandled = True
    elif nValue == ROS_LED_BLUE:
        LedPwm(0, 100)
        IsHandled = True
    elif nValue == ROS_LED_MAGENTA:
        LedPwm(100, 100)
        IsHandled = True

    return IsHandled

# 각도를 모터에서 사용하는 Data 로 바꾸어 주는 함수(float -> int)
# (English) Function to convert the degree of DYNAMIXEL to the data unit (float to int)
def CalcAngle2Raw(fAngle) :
    if fAngle == None :
        fAngle = 0.0
    return (int)(round(fAngle * 4096.0 / 360.0 + 2048.0))

# 모터에서 사용하는 Data를 각도값으로 바꾸어 주는 함수(int -> float)
# (English) Function to convert data unit to the degree of DYNAMIXEL.
def CalcRaw2Angle(nRaw) :
    if nRaw == None :
        nRaw = 0
    return (float)(360.0 * ((nRaw - 2048.0) / 4096.0))
def Offset_GetData(nID):
    nValue = etc.read16(200 + nID * 2)
    if (nValue > 32767) :
        nValue = (65536 - nValue) * -1
    return int(nValue)
def Offset_Read() :
    global aOffset
    etc.write8(199,1)
    delay(50)
    nMot_First = 17
    nMot_Cnt = 1
    for i in range(nMot_First,nMot_First + nMot_Cnt):
        nID = i
        aOffset[nID] = Offset_GetData(nID)
def Offset_Write() :
    etc.write8(199,2)
def Offset_Clear() :
    global aOffset
    etc.write8(199,3)
    nCnt = len(aOffset)
    aOffset = [0] * nCnt
def Test1(nBackgroundImage = 1, nImage = 0, x=500,y=500):
    pass

#모터의 동작 속도를 세팅(Position 기준) : 0 초기화
# (English) Set the operating velocity (Position Mode) : 0 means reset.
def Setup_Speed(nID, nValue) :
    DXL(nID).write32(112, nValue)

#모든 모터를 가운데 정렬한다.(Motion_Offset)
# (English) Align center all DYNAMIXEL (Motion Offest).
def Move_Center(IsOffset = False) :
    #profile 속도 조정
    # (English) Profile Velocity adjustment.    
    Setup_Speed(254, 20)
    etc.write8(1200,0)
    etc.write16(1202,116)
    etc.write8(1204,4)
    nMot_First = 1
    nMot_Cnt = 17
    for i in range(nMot_First,nMot_First + nMot_Cnt):
        nID = i
        nValue = 0
        if (IsOffset) :
            nValue = Offset_GetData(nID)
        etc.write8(1205,nID)
        etc.write32(1206,2048 + nValue)
        etc.write8(1200,1)
    etc.write8(1200,2)
    #profile 속도 복원
    # (English) Profile Velocity recovery
    Setup_Speed(254, 0)
    #모든 모터를 가운데 정렬한다.(Motion_Offset)
    # (English) Align center all DYNAMIXEL (Motion Offest).
def TestMove(nID, fAngle, nSpeed = -1, IsOffset = False) :
    if (nSpeed >= 0):
        Setup_Speed(nID, nSpeed)
    DXL(nID).write32(116, CalcAngle2Raw(fAngle) + aOffset[nID])
    tmr = CTimer()
    tmr.Set()
    nPass = 0
    while(True) :
        nMoving = DXL(nID).read8(122)
        if ((tmr.Get() >= 200) and (nPass == 0)) :
            break
        elif (nMoving != 0) :
            nPass = 1
        elif ((nMoving == 0) and (nPass == 1)) :
            nPass = 2
            break
def WaitButtonUp(nTouchMode = 0): # 0 : All, 1 : FirstTouch, 2 : SecondTouch
    while(True) :
        # 버튼 눌림 체크
        # (English) Checking the button push
        nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1 = GetButton(btnList)
        if (nTouchMode == 1):
            if (nNum0 < 0):
                break
        if (nTouchMode == 2):
            if (nNum1 < 0):
                break
        else:
            if ((nNum0 < 0) and (nNum1 < 0)):
                break
def GetButton(btns):
    #스마트폰의 터치 입력을 확인
    # (English) Checking the input touch on the smart device.    
    GetTouch_Down()

    nNum0 = -1
    nNum1 = -1
    nDown0 = 0
    nDown1 = 0
    nUp0 = 0
    nUp1 = 0
    Btn0 = None
    Btn1 = None
    nNum = 0
    nCnt = 0
    if (CVar.nTouch_Pos0 > 0) :
        nCnt = nCnt + 1
    if (CVar.nTouch_Pos1 > 0) :
        nCnt = nCnt + 1
    nPass = 0
    for btn in btns:
        if (CVar.nTouch_Pos0 > 0):
            if (IsButton(CVar.nTouch_XY_X0, CVar.nTouch_XY_Y0, btn) == True) :
                nNum0 = btn[_BTN_INDEX]
                Btn0 = btn
                nPass = nPass | 0x01
        if (CVar.nTouch_Pos1 > 0):
            if (IsButton(CVar.nTouch_XY_X1, CVar.nTouch_XY_Y1, btn) == True) :
                nNum1 = btn[_BTN_INDEX]
                Btn1 = btn
                nPass = nPass | 0x10
        if (nCnt == 1) :
            if (nPass > 0):
                break
        else:
            if (nPass == 0x11):
                break
        nNum = nNum + 1
    if ((nNum1 == nNum0) and (nNum0 >= 0)):
        nNum1 = -1
    # switching
    if (((nNum0 >= 0) and (nNum0 == CVar.nButton_1)) or ((nNum1 >= 0) and (nNum1 == CVar.nButton_0))) :
        nNum2 = nNum1
        nNum1 = nNum0
        nNum0 = nNum2
    #Button Down Event
    if (nNum0 >= 0):
        if (CVar.nButton_0 != nNum0):
            nDown0 = 1
        CVar.btn0 = Btn0
    else :
        if (CVar.nButton_0 >= 0):
            nUp0 = 1
    if (nNum1 >= 0):
        if (CVar.nButton_1 != nNum1):
            nDown1 = 1
        CVar.btn1 = Btn1
    else :
        if (CVar.nButton_1 >= 0):
            nUp1 = 1
    CVar.nButton_0 = nNum0
    CVar.nButton_1 = nNum1
    if nUp0 == 1:
        Btn0 = CVar.btn0
    if nUp1 == 1:
        Btn1 = CVar.btn1
    return nNum0, nNum1, nDown0, nDown1, nUp0, nUp1, Btn0, Btn1
def CheckButton(Btn0, Btn1, Btn) :
    if (Btn0 == Btn) :
        return 1
    elif (Btn1 == Btn) :
        return 2
    return 0
def CheckButton_Event(Btn0, Btn1, nEvent0, nEvent1, Btn) :
    if (Btn0 == Btn) :
        if (nEvent0 > 0):
            return 1
    elif (Btn1 == Btn) :
        if (nEvent1 > 0):
            return 2
    return 0
def Page_MenuBar(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1):
    if (Btn0 == _BTN_SUB_OUT):
        ShowPage(CVar.nPage_Prev)
    #메뉴가 나타난 상태에서 바깥 부분을 누를 경우
    # (English) If clicking on the side out of the menu section while it's being displayed.         
    elif (Btn0 == _BTN_SUB_REMOTE):
        ShowPage(_PAGE_REMOTE_NORMAL)
    elif (Btn0 == _BTN_SUB_STREAM):
        ShowPage(_PAGE_STREAM)
    elif (Btn0 == _BTN_SUB_FACE_TRACK):
        ShowPage(_PAGE_FACE_TRACK)
    elif (Btn0 == _BTN_SUB_MOTOR):
        ShowPage(_PAGE_MOTOR_TEST)
    elif (Btn0 == _BTN_SUB_OFFSET):
        ShowPage(_PAGE_OFFSET)
    elif (Btn0 == _BTN_SUB_X):
        ShowPage(CVar.nPage_Prev)
    #스마트폰의 터치 입력을 확인    
    if ((nNum0 >= 0) or (nNum1 >= 0)):
        WaitButtonUp()
#무릎의 ID = 15, 16
# Knee ID = 15, 16
def CheckKnee() :
    CVar.nKnee = 0
    fAngle = CalcRaw2Angle(DXL(15).present_position())
    if (fAngle > 100.0) :
        CVar.nKnee = CVar.nKnee + 1
    # 조립 방향이 반대이므로 각도환산시 부호를 (-) 를 해주면(뒤집으면) 같은 방향의 해석이 가능하다.    
    # (English) As The assembly direction is opposite, in converting angle you can simply translate the opposite direction by adding (-) sign.    
    fAngle = -CalcRaw2Angle(DXL(16).present_position())
    if (fAngle > 100.0) :
        CVar.nKnee = CVar.nKnee + 1
def CheckTouch_for_walking(nDirection):
    CVar.nWalking = 0
    if ((nDirection >= 12) and (nDirection <= 14)) :
        # 12 (forward-left) 13 (forward) 14 (forward-right)
        CVar.nWalking = 1
    elif ((nDirection >= 17) and (nDirection <= 19)) :
        # 17 (Backward-left) 18 (Backward) 19 (Backward-right)
        CVar.nWalking = -1
def walking(nDirection) :
    CVar.nWalking = 0
    if (nDirection > 0):
        CheckTouch_for_walking(nDirection)
        nMotion = 0
        nMotion_Next = 0
        _MOTION_KNEE = 201
        _MOTION = 101
        if (CVar.nPage == _PAGE_REMOTE_SPECIAL):
            _MOTION_KNEE = 301
            _MOTION = 301
            CVar.nSpeed = 0
        if (CVar.nWalking != 0):
            if (CVar.nKnee > 0):
                nMotion = _MOTION_KNEE - (CVar.nWalking - 1) * 5 / 2
                nMotion_Next = _MOTION_KNEE - (CVar.nWalking - 1) * 5 / 2 + (nDirection - 11) % 5
            else :
                nMotion = _MOTION + CVar.nSpeed * 50 - (CVar.nWalking - 1) * 5 / 2
                nMotion_Next = _MOTION + CVar.nSpeed * 50  - (CVar.nWalking - 1) * 5 / 2 + (nDirection - 11) % 5
            Motion_Play(nMotion, nMotion_Next)
            nCnt = 0
            CVar.nWalking_Prev = CVar.nWalking
            while(CVar.nWalking != 0) :
                IsPunch = False
                while(motion.status() == True):
                    # 조종모드
                    # Remote Control Mode                    
                    nDirection = 0
                    if (btnList != None):
                        nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1 = GetButton(btnList)
                        if CheckButton(Btn0, Btn1, _BTN_MOVE_UL) :
                            nDirection = 12
                        if CheckButton(Btn0, Btn1, _BTN_MOVE_U) :
                            nDirection = 13
                        if CheckButton(Btn0, Btn1, _BTN_MOVE_UR) :
                            nDirection = 14
                        if CheckButton(Btn0, Btn1, _BTN_MOVE_DL) :
                            nDirection = 17
                        if CheckButton(Btn0, Btn1, _BTN_MOVE_D) :
                            nDirection = 18
                        if CheckButton(Btn0, Btn1, _BTN_MOVE_DR) :
                            nDirection = 19
                        if CheckButton(Btn0, Btn1, _BTN_ACT_01) :
                            IsPunch = True
                    CheckTouch_for_walking(nDirection)
                if (CVar.nWalking != 0):
                    if (CVar.nWalking != CVar.nWalking_Prev):
                        CVar.nWalking = CVar.nWalking_Prev
                        break
                    nCnt = 1
                else :
                    nCnt = 0
                if (nCnt > 0) :
                    nCnt = nCnt - 1
                else :
                    break
                if (IsPunch):
                    break
                else:
                    # ready: 100, start: 101, left: 102, go: 103, right: 104, end: 105
                    if (CVar.nKnee > 0):
                        nMotion = _MOTION_KNEE - (CVar.nWalking - 1) * 5 / 2 + (nDirection - 11) % 5
                        nMotion_Next = nMotion
                    else :
                        nMotion = _MOTION + CVar.nSpeed * 50 - (CVar.nWalking - 1) * 5 / 2 + (nDirection - 11) % 5
                        nMotion_Next = nMotion
                    Motion_Play(nMotion, nMotion_Next)
                    CVar.nWalking_Prev = CVar.nWalking
            if (CVar.nWalking_Prev != CVar.nWalking):
                CVar.nWalking = CVar.nWalking_Prev
            if (IsPunch):
                nMotion = 80
            else:
                if (CVar.nKnee > 0):
                    nMotion = (_MOTION_KNEE + 4) - (CVar.nWalking - 1) * 5 / 2
                else :
                    nMotion = (_MOTION + 4) + CVar.nSpeed * 50 - (CVar.nWalking - 1) * 5 / 2
            Motion_Play_And_Wait(nMotion)
            if (CVar.nPage != _PAGE_REMOTE_FIGHT) and (CVar.nPage != _PAGE_STREAM) and (CVar.nPage != _PAGE_REMOTE_SPECIAL):
                Motion_Play_And_Wait(16)
def Filter_LowPass(fWeight, fVal_Curr, fVal_Prev) :
    return int(round(float(fVal_Curr) * fWeight + (1.0 - fWeight) * float(fVal_Prev), 0))
def Page_Remote(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1):
    global nMotion_Prev
    # Remote control mode 에서 각 페이지 전환
    # (English) Page change over in Remote control mode    
    if Event_Dn0 == 1:
        IsShowPage = True
        if (Btn0 == _BTN_REMOTE_NORMAL):
            ShowPage(_PAGE_REMOTE_NORMAL)
        elif (Btn0 == _BTN_REMOTE_FIGHT):
            ShowPage(_PAGE_REMOTE_FIGHT)
        elif (Btn0 == _BTN_REMOTE_SPECIAL):
            ShowPage(_PAGE_REMOTE_SPECIAL)
        else:
            IsShowPage = False
        if IsShowPage == True:
            #페이지가 바뀌면서 버튼의 이벤트가 재설정되기 때문에 이벤트가 다시 한번 발생할 수 있어
            #페이지가 바뀌기 전에 버튼을 뗄때까지 대기하는 대기문을 작성해야 한다.
            # (English) Have a functop to wait a button-off before page's change over to prevent repeating event (as the button event is reset when the page's change over.)            
            WaitButtonUp(1) # 버튼에서 손을 뗄 때까지 대기 # (English) Wait until hand-off out of the button pushed.
    
    #토크 ON/OFF 버튼 - 토크오프는 주의해야할 기능이기 때문에 반드시 터치가 하나만 들어올때 동작하도록 한다.
    # (English) Button for Torque ON / OFF. As using the Torque OFF should be treated with an extra care, be sure to use it in a single touch ONLY.    
    if (Btn0 == _BTN_TORQ):
        if Event_Dn0 == 1:
            tmrTorqBtn.Set()
            if (CVar.IsTorqOn == True):
                #토크를 풀기전에 앉아준다.
                # (English) Sit down before Torque OFF.                 
                Motion_Play_And_Wait(60)
                delay(100)
                TorqAll(False, True)
                nMotion_Prev = 0
            else :
                TorqAll(True, True)
                if (CVar.nPage == _PAGE_REMOTE_FIGHT) or (CVar.nPage == _PAGE_STREAM):
                    Motion_Ready(2)
                else:
                    Motion_Ready(1)
        elif Event_Up0 == 1:
            tmrTorqBtn.Destroy()
        # 계속 누르고 있다면
        # (English) If holding on the button continuosly        
        else:
            #Reboot All
            if (tmrTorqBtn.Get() >= 3000):
                #Command - Reboot
                dxlbus.reboot()
                #Reboot - Beep
                buzzer.melody(1)
                #TorqOff variable
                CVar.IsTorqOn = False
                #더이상 타이머 감지를 하지 않는다.
                # (English) Stop detecting the timer.                
                tmrTorqBtn.Destroy()
    if CheckButton_Event(Btn0, Btn1, Event_Dn0, Event_Dn1, _BTN_LED):
        Led()
    if CheckButton(Btn0, Btn1, _BTN_GETUP):
        GetUp()
    #Special Page 에서는 속도조정을 하지 않는다.
    # (English) Special Page does not adjust speed.        
    if (CVar.nPage != _PAGE_REMOTE_SPECIAL):
        if ((Btn0 == _BTN_SPD) and (Event_Dn0 == 1)) or ((Btn1 == _BTN_SPD) and (Event_Dn1 == 1)):
            CVar.nSpeed = (CVar.nSpeed + 1) % 2
            Show_Background((CVar.nPage*2) + CVar.nSpeed - 1)
    ######################################################
    # 조종모드
    # (English) Remote Control Mode    
    nDirection = 0
    if CheckButton(Btn0, Btn1, _BTN_MOVE_UL) :
        nDirection = 12
    if CheckButton(Btn0, Btn1, _BTN_MOVE_U) :
        nDirection = 13
    if CheckButton(Btn0, Btn1, _BTN_MOVE_UR) :
        nDirection = 14
    if CheckButton(Btn0, Btn1, _BTN_MOVE_DL) :
        nDirection = 17
    if CheckButton(Btn0, Btn1, _BTN_MOVE_D) :
        nDirection = 18
    if CheckButton(Btn0, Btn1, _BTN_MOVE_DR) :
        nDirection = 19
    walking(nDirection)
    ######################################################
    if nDirection == 0:
        nAction = 0
        # 좌/우회전
        # (English) Left/Right turn        
        if CheckButton(Btn0, Btn1, _BTN_TURN_L):
            if (CVar.nPage == _PAGE_REMOTE_SPECIAL):
                nAction = 90
            else:
                nAction = 50 + CVar.nSpeed * 2
        elif CheckButton(Btn0, Btn1, _BTN_TURN_R):
            if (CVar.nPage == _PAGE_REMOTE_SPECIAL):
                nAction = 91
            else:
                nAction = 51 + CVar.nSpeed * 2
        ######################################################
        # 대각이동
        # (English) Diagonal walk
        # ↖                 
        elif CheckButton(Btn0, Btn1, _BTN_MOVE_DG_FL):
            if (CVar.nPage == _PAGE_REMOTE_SPECIAL):
                nAction = 94
            else:
                nAction = 70
        # ↗                
        elif CheckButton(Btn0, Btn1, _BTN_MOVE_DG_FR):
            if (CVar.nPage == _PAGE_REMOTE_SPECIAL):
                nAction = 95
            else:
                nAction = 71
        # ↙                
        elif CheckButton(Btn0, Btn1, _BTN_MOVE_DG_BL):
            if (CVar.nPage == _PAGE_REMOTE_SPECIAL):
                nAction = 96
            else:
                nAction = 72
        # ↘                
        elif CheckButton(Btn0, Btn1, _BTN_MOVE_DG_BR):
            if (CVar.nPage == _PAGE_REMOTE_SPECIAL):
                nAction = 97
            else:
                nAction = 73
        ######################################################
        # 옆걸음
        # (English) Side walk                
        elif CheckButton(Btn0, Btn1, _BTN_MOVE_L):
            if (CVar.nPage == _PAGE_REMOTE_SPECIAL):
                nAction = 92
            else:
                nAction = 54 + CVar.nSpeed * 2 # left
        elif CheckButton(Btn0, Btn1, _BTN_MOVE_R):
            if (CVar.nPage == _PAGE_REMOTE_SPECIAL):
                nAction = 93
            else:
                nAction = 55 + CVar.nSpeed * 2 # right      
        ######################################################                
        elif (CVar.nPage == _PAGE_REMOTE_NORMAL):
            if CheckButton(Btn0, Btn1, _BTN_ACT_01):
                nAction = 5
            elif CheckButton(Btn0, Btn1, _BTN_ACT_02):
                nAction = 6
            elif CheckButton(Btn0, Btn1, _BTN_ACT_03):
                nAction = 7
            elif CheckButton(Btn0, Btn1, _BTN_ACT_04):
                nAction = 8
            elif CheckButton(Btn0, Btn1, _BTN_ACT_05):
                nAction = 10
            elif CheckButton(Btn0, Btn1, _BTN_ACT_06):
                nAction = 12
            elif CheckButton(Btn0, Btn1, _BTN_ACT_07):
                nAction = 9
            elif CheckButton(Btn0, Btn1, _BTN_ACT_08):
                nAction = 11
        elif (CVar.nPage == _PAGE_REMOTE_FIGHT):
            if CheckButton(Btn0, Btn1, _BTN_ACT_01):
                nAction = 21
                Move_Offset1(17, smart.sensor.tilt_right() - smart.sensor.tilt_left())
                Move_Offset1(3, smart.sensor.tilt_down() - smart.sensor.tilt_up())
            elif CheckButton(Btn0, Btn1, _BTN_ACT_02):
                nAction = 22
                Move_Offset1(17, smart.sensor.tilt_right() - smart.sensor.tilt_left())
                Move_Offset1(1, smart.sensor.tilt_up() - smart.sensor.tilt_down())
            elif CheckButton(Btn0, Btn1, _BTN_ACT_03):
                nAction = 23
            elif CheckButton(Btn0, Btn1, _BTN_ACT_04):
                nAction = 24
            elif CheckButton(Btn0, Btn1, _BTN_ACT_05):
                nAction = 25
            if CheckButton(Btn0, Btn1, _BTN_ACT_06):
                nAction = 26
            if CheckButton(Btn0, Btn1, _BTN_ACT_07):
                nAction = 27
            if CheckButton(Btn0, Btn1, _BTN_ACT_08):
                nAction = 28
            if CheckButton(Btn0, Btn1, _BTN_ACT_09):
                WaitButtonUp()
                Defense(20)
            if CheckButton(Btn0, Btn1, _BTN_ACT_10):
                nAction = 29
        elif (CVar.nPage == _PAGE_STREAM):
            if CheckButton(Btn0, Btn1, _BTN_ACT_01):
                nAction = 21
            elif CheckButton(Btn0, Btn1, _BTN_ACT_02):
                nAction = 22
            elif CheckButton(Btn0, Btn1, _BTN_ACT_03):
                nAction = 23
            elif CheckButton(Btn0, Btn1, _BTN_ACT_04):
                nAction = 24
            elif CheckButton(Btn0, Btn1, _BTN_ACT_05):
                nAction = 25
            if CheckButton(Btn0, Btn1, _BTN_ACT_06):
                nAction = 26
            if CheckButton(Btn0, Btn1, _BTN_ACT_07):
                nAction = 27
            if CheckButton(Btn0, Btn1, _BTN_ACT_08):
                nAction = 28
        elif (CVar.nPage == _PAGE_REMOTE_SPECIAL):
            if CheckButton(Btn0, Btn1, _BTN_ACT_01):
                pass
            if CheckButton(Btn0, Btn1, _BTN_ACT_02):
                pass
            if CheckButton(Btn0, Btn1, _BTN_ACT_03):
                pass
            if CheckButton(Btn0, Btn1, _BTN_ACT_04):
                pass
        if (nAction > 0):
            if (CVar.nPage == _PAGE_REMOTE_NORMAL):
                if (nMotion_Prev <= 1):
                    if (nAction >= 50):
                        Motion_Play_And_Wait(2)
            if (CVar.nPage == _PAGE_REMOTE_NORMAL):
                LedPwm(50, 100)
            Motion_Play_And_Wait(nAction)
            if (CVar.nPage == _PAGE_REMOTE_FIGHT):
                for i in range(1,18):
                    Move_Offset1(i, 0)
            if (CVar.nPage == _PAGE_REMOTE_NORMAL):
                LedPwm(0, 0)
        else:
            if (CVar.nPage == _PAGE_REMOTE_NORMAL):
                if (nMotion_Prev >= 50):
                    Motion_Play_And_Wait(16)
            nMotion_Prev = 0
m_IsFind = False
def Page_Face_Track(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1):
    global m_IsFind
    CVar.m_nPwm = (CVar.m_nPwm + 10) % 200
    Value = CVar.m_nPwm - CVar.m_nPwm % 100 * int(CVar.m_nPwm / 100) * 2
    if (rpi.area() > 0) :
        Show_Text(500,500,1, _COLOR_BLUE, 140)
        #로봇이 좌측을 보는 값이 x 값이 0 으로 수렴
        # (English) The value of X (Robot's left view) converges 0        
        nPos_X = rpi.position_x() - 320/2
        #아래가 y 가 0으로 수렴
        # (English) The value of y converges 0
        nCenterGap = 0
        if ( nPos_X < (-20 + nCenterGap) ) :
            CVar.nPos_Servo += 1
            CVar.IsTurning_Face = True
        elif (nPos_X > (20 + nCenterGap) ) :
            CVar.nPos_Servo -= 1
            CVar.IsTurning_Face = True
        else:
            CVar.IsTurning_Face = False
        if CVar.IsTurning_Face == True:
            if (CVar.nPos_Servo > 512 + 200) :
                CVar.nPos_Servo = 512 + 200
            elif (CVar.nPos_Servo < 512 - 200) :
                CVar.nPos_Servo = 512 - 200
            OLLO(1, const.OLLO_JOINT_POSITION).write(CVar.nPos_Servo)
        else:
            if (m_IsFind == False):
                if motion.status() == False:
                    Motion_Play(14)
            m_IsFind = True
        LedPwm(0, Value)
    else:
        Show_Text(500,500,0)
        LedPwm(Value, 0)
        m_IsFind = False
def Page_MotorTest(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1):
    if (Event_Dn0 == 1):
        nID = -1
        #첫번째 액츄에이터의 인덱스를 가져온다.
        # (English) Bring the first DYNAMIXEL index.         
        nFirstIndex = _BTN_ID_01[4]
        for i in range(0,18):
            nButtonIndex = i + nFirstIndex
            if (nButtonIndex == nNum0) or (nButtonIndex == nNum1):
                nID = i + 1
        if nID >= 0:
            Show_Motors(nID)
            #모든 LED Off
            # (English) Light off all LED.            
            DXL(254).write8(65, 0)
            #선택된 모터의 LED On
            # (English) LED On of selected DYNAMIXEL.            
            DXL(nID).write8(65, 1)
            fRange = 10
            # test moving
            TestMove(nID, 0, 30)
            TestMove(nID, fRange, 30)
            TestMove(nID, -fRange, 30)
            TestMove(nID, 0, 30)
            Setup_Speed(nID, 0)
def Page_Offset(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1):
    if (Event_Dn0 == 1):
        nID = -1
        #첫번째 액츄에이터의 인덱스를 가져온다.
        # (English) Bring the first DYNAMIXEL index.         
        nFirstIndex = _BTN_ID_01[4]
        for i in range(0,18):
            nButtonIndex = i + nFirstIndex
            if (nButtonIndex == nNum0) or (nButtonIndex == nNum1):
                nID = i + 1
        if (nID >= 0):
            Show_Motors(nID)
            #모든 LED Off
            # (English) Light off all LED.            
            DXL(254).write8(65, 0)
            #선택된 모터의 LED On
            # (English) LED On of selected DYNAMIXEL.            
            DXL(nID).write8(65, 1)
            CVar.nID = nID
            CVar.nOffset = Offset_GetData(nID)
            ShowPage(_PAGE_OFFSET_DIALOG1)
            WaitButtonUp()
        else:
            CVar.nID = -1
            if (Btn0 == _BTN_RESET):
                ShowPage(_PAGE_OFFSET_DIALOG2)
                WaitButtonUp()
                CVar.IsResetCommand = True
            elif (Btn0 == _BTN_INIT):
                TorqAll(True,False)
                Move_Center(True)
def Page_Offset_Dialog_1(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1):
    if (Btn0 == _BTN_DIALOG_PLUS):
        if (DXL(CVar.nID).read8(64) == 0):
            #Torq Off -> On
            TorqOnOff(CVar.nID, True, False)
            Show_Image(600, 400, 53)
        CVar.nOffset = CVar.nOffset + 1
        etc.write16(200 + CVar.nID * 2, (int)(CVar.nOffset))
        DXL(CVar.nID).goal_position(2048 + (int)(CVar.nOffset))
    if (Btn0 == _BTN_DIALOG_MINUS):
        if (DXL(CVar.nID).read8(64) == 0):
            #Torq Off -> On
            TorqOnOff(CVar.nID, True, False)
            Show_Image(600, 400, 53)
        CVar.nOffset = CVar.nOffset - 1
        etc.write16(200 + CVar.nID * 2, (int)(CVar.nOffset))
        DXL(CVar.nID).goal_position(2048 + (int)(CVar.nOffset))
    if (CVar.nID > 0):
        Show_Num_Offset(CVar.nID)
    if (Event_Dn0 == 1):
        if (Btn0 == _BTN_DIALOG_OK):
            if (DXL(CVar.nID).read8(64) == 0):
                CVar.nOffset = DXL(CVar.nID).goal_position() - 2048
            # Offset 데이타를 넣어 줌
            # (English) Add offset data.            
            etc.write16(200 + CVar.nID * 2, (int)(CVar.nOffset))
            # Save            
            ShowPage(_PAGE_OFFSET_DIALOG2)
            TorqAll(True, False)
        if (Btn0 == _BTN_DIALOG_CANCEL):
            ShowPage(_PAGE_OFFSET)
        if (Btn0 == _BTN_DIALOG_TORQ):
            if (CVar.nID > 0) :
                if (DXL(CVar.nID).read8(64) == 0):
                    #Torq Off -> On
                    TorqOnOff(CVar.nID, True)
                    Show_Image(600, 400, 53)
                    CVar.nOffset = DXL(CVar.nID).goal_position() - 2048
                    etc.write16(200 + CVar.nID * 2, (int)(CVar.nOffset))
                else :
                    #Torq On -> Off
                    TorqOnOff(CVar.nID, False)
                    Show_Image(600, 400, 54)
                etc.write16(200 + CVar.nID * 2, (int)(CVar.nOffset))
def Page_Offset_Dialog_2(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1):
    global aOffset
    if (Event_Dn0 == 1):
        if (Btn0 == _BTN_DIALOG_OK):
            if (CVar.IsResetCommand == True):
                Offset_Clear()
            else :
                Offset_Write()
                aOffset[CVar.nID] = CVar.nOffset
            # Done - Close the dialog
            ShowPage(_PAGE_OFFSET)
            Move_Center(True)
        if (Btn0 == _BTN_DIALOG_CANCEL):
            ShowPage(_PAGE_OFFSET)
def Show_Dialog(nStep, nID=5) :
    # Show Offset Dialog
    if (nStep == 1) :
        CVar.IsResetCommand = False
        # 대화상자 배경 표시
        # (English) Background image of the dialog box.        
        Show_Image(500, 500, 51)
        #Torq On/Off Image  
        Show_Image(600, 400, 53)
        #DXL ID 표시
        # (English) Display DYNAMIXEL ID.        
        Show_Num(475, 210, nID, _COLOR_WHITE, 80)
    #Show Save Dialog    
    elif (nStep == 2) :
        #전체 숫자 지움
        # (English) Delete all numbers.        
        Clear_Num()
        # 대화상자 배경 표시
        # (English) Background image of the dialog box.        
        Show_Image(500, 500, 52)
        #DXL ID 표시
        # (English) Display DYNAMIXEL ID.        
        Show_Num(475, 210, nID, _COLOR_WHITE, 80)
        #SAVE 문자 출력
        # (English) Display SAVE characters        
        Show_Text(500,500,11,_COLOR_BLACK,100)
    else :
        CVar.IsResetCommand = False
        #Clear - 대화상자 배경
        Show_Image(500, 500, 0)
        #Clear - Torq On/Off Image  
        Show_Image(600, 400, 0)
        #Clear - Show Text Save
        Show_Text(500,500,0)
        #전체 숫자 지움
        # (English) Delete all numbers.        
        Clear_Num()
        #창을 닫으면 Torq On -> Move Center 를 하도록 한다.        
        TorqAll(True, False)
        if (CVar.nPage == _PAGE_OFFSET):
            Move_Center(True)
        else :
            Move_Center()
def Show_Num_Offset(nID) :
    nOffset = DXL(nID).goal_position() - 2048
    nColor = 5
    nGap = 30
    if (nOffset < 0) :
        nOffset = -nOffset
        nColor = 3
    nPos_X = 420
    nPos_Y = 560
    nSize = 0
    for j in range(0, 4) :
        if (nOffset < pow(10, (j + 1))) :
            for i in range(0, 4 - j) :
                # Show_Num 의 Size 를 0 으로 해서 지울수도 있으나 가독성을 위해 Clear_Num() 함수를 만들어 사용     
                # (English) Clear_Num() is created for the purpose of readable code, although it could clear Size of Show_Num with 0.  
                Clear_Num(nPos_X + nGap * i, nPos_Y)
                         
            break
    nSize = 120
    for i in range(0, 5) :
        j = (int)(pow(10, (4 - i)))
        # 1 의 자리(i == 4)는 상시 표기해야 하니 if 문에 걸리지 않도록 or 조건으로 묶어준다. 
        # (English) (i==4) is used with logical OR operator for letting If condition ignore it because the unit's place should constantly be marked.
        if (nOffset >= j) or (i == 4) : 
            nValue = (int)(nOffset / j) % 10
            Show_Num(nPos_X + nGap * i, nPos_Y, nValue, nColor, nSize)
def Move_Offset1(nID, fAngle):
    etc.write16(264 + nID * 2, CalcAngle2Raw(fAngle)-2048)
def Move_Offset2(nID0, nRaw0, nID1, nRaw1):
    etc.write16(264 + nID0 * 2, nRaw0-2048)
    etc.write16(264 + nID1 * 2, nRaw1-2048)
def Defense(nMotion):
    nVal_Prev = 0
    pitch_knee_Prev = 0
    pitch_Up_Prev = 0
    pitch_Arm_Prev = 0
    nAction = 0
    Limit_Roll = 20
    Limit_Pitch = 20
    Sensing_Roll = 10
    Sensing_Pitch = 6
    nErrorCnt = 100
    while True:
        # 버튼 눌림 체크
        # (English) Checking the button push        
        nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1 = GetButton(btnList)
        if nNum0 >= 0 or nNum1 >= 0:
            break
        motion.play(nMotion)
        while True:
            if motion.status() == True:
                roll = imu.roll()/100.0
                pitch = imu.pitch()/100.0
                nAction = 0
                if (roll > Sensing_Roll):
                    nAction = 57 # right - 넘어지는 방향으로 도망. # (English) Right - Run to the direction where falling down.
                elif (roll < -Sensing_Roll):
                    nAction = 56 # left - 넘어지는 방향으로 도망 # (English)Left - Run to the direction where falling down.
                if nAction > 0:
                    Motion_Stop()
                    while motion.status():
                        pass
                    Motion_Play_And_Wait(nAction)
                    for i in range(1,17):
                        Move_Offset1(i, 0)
                    Motion_Play_And_Wait(nMotion)
                else:
                    if (roll > Limit_Roll):
                        roll = Limit_Roll
                    elif (roll < -Limit_Roll):
                        roll = -Limit_Roll
                    if (pitch > Limit_Pitch):
                        pitch = Limit_Pitch
                    elif (pitch < -Limit_Pitch):
                        pitch = -Limit_Pitch
                    roll_Up = -roll * 2.0
                    weight_roll = 1.7 #1.2 # 반대다리 # (English) Opposite leg
                    weight_roll_Stand = 2.7 # 3 # 기준다리 # (English) Standing leg
                    weight_roll_w = 2.0
                    Val_L = 2048
                    Val_R = 2048
                    if (roll_Up >= 0):
                        Val_L = CalcAngle2Raw(roll_Up / weight_roll_Stand)
                        Val_R = CalcAngle2Raw(roll_Up * weight_roll)
                        Move_Offset1(2, roll_Up * weight_roll_w)
                    else :
                        Val_L = CalcAngle2Raw(roll_Up * weight_roll)
                        Val_R = CalcAngle2Raw(roll_Up / weight_roll_Stand)
                        Move_Offset1(4, -roll_Up * weight_roll_w)
                    Move_Offset2(5, Val_R, 7, Val_L)
                    Val2 = CalcAngle2Raw(roll_Up / 3) #2048#CalcAngle2Raw(-roll_Up / 4)
                    Move_Offset2(10, Val2, 12, Val2)
                    pitch_Up = pitch
                    #고관절
                    # (English) Hip joint
                    pitch_Up_Filter = pitch_Up * 3
                    if (pitch_Up_Prev == 0) :
                        pitch_Up_Prev = pitch_Up_Filter
                    pitch_Up_Filter = Filter_LowPass(0.5, pitch_Up_Filter, pitch_Up_Prev)
                    pitch_Up_Prev = pitch_Up_Filter
                    Val = CalcAngle2Raw(pitch_Up_Filter)
                    Val2 = CalcAngle2Raw(-pitch_Up_Filter)
                    Move_Offset2(6, Val, 8, Val)
                    # 팔
                    # (English) Arms                    
                    nArm_Multi = 3
                    if abs(pitch_Up) < 5 :
                        nArm_Multi = 4
                    pitch_Arm_Filter = pitch_Up * nArm_Multi
                    if (pitch_Arm_Prev == 0) :
                        pitch_Arm_Prev = pitch_Arm_Filter
                    pitch_Arm_Filter = Filter_LowPass(0.6, pitch_Arm_Filter, pitch_Arm_Prev)
                    pitch_Arm_Prev = pitch_Arm_Filter
                    Val = CalcAngle2Raw(pitch_Arm_Filter)
                    Val2 = CalcAngle2Raw(-pitch_Arm_Filter)
                    Move_Offset2(1, Val2, 3, Val)
                    #발목
                    # (English) Ankles                    
                    pitch_Dn_Filter = -pitch_Up*2
                    if (nVal_Prev == 0) :
                        nVal_Prev = pitch_Dn_Filter
                    pitch_Dn_Filter = Filter_LowPass(0.6, pitch_Dn_Filter, nVal_Prev)
                    nVal_Prev = pitch_Dn_Filter
                    Val2 = CalcAngle2Raw(pitch_Dn_Filter)
                    Move_Offset2(9, Val2, 11, Val2)
                    
                    #무릎
                    # (English) Knees                    
                    pitch_knee = pitch_Up*1
                    if (pitch_knee_Prev == 0) :
                        pitch_knee_Prev = pitch_knee
                    pitch_knee = Filter_LowPass(0.6, pitch_knee, pitch_knee_Prev)
                    pitch_knee_Prev = pitch_knee
                    Val_Knee_0 = CalcAngle2Raw(pitch_knee)
                    Val_Knee_1 = CalcAngle2Raw(-pitch_knee)
                    Move_Offset2(15, Val_Knee_0, 16, Val_Knee_1)
                    nLimit_Defense_Front = 2150-(50) # - 는 둔감 + 는 민감 # (English) - : Decreasing sensitivity + : increasing sensitivity
                    nLimit_Defense_Back = 1900+(-10) # - 는 둔감 + 는 민감 # (English) - : Decreasing sensitivity + : increasing sensitivity
                    if (nErrorCnt > 0):
                        nErrorCnt = nErrorCnt - 1
                        nLimit_Defense_Back = nLimit_Defense_Back - 1000
                        nLimit_Defense_Front = nLimit_Defense_Front + 1000
                    nAction = 0
                    # 앞으로 넘어지는 경우 Val2가 감소한다.(뒤에서 친 경우)
                    # (English) Val2 decrease in falling down to front.
                    if (Val2 < nLimit_Defense_Back):
                        nErrorCnt = 100
                        Motion_Stop()
                        if roll >= 0 :
                            nAction = 71
                        else:
                            nAction = 70
                    elif (Val2 > nLimit_Defense_Front):
                        nErrorCnt = 100
                        Motion_Stop()
                        if roll >= 0 :
                            nAction = 73
                        else:
                            nAction = 72
                    if nAction > 0:
                        while motion.status():
                            pass
                        Motion_Play_And_Wait(nAction)
            else:
                break
    buzzer.melody(14)
    for i in range(1,17):
        Move_Offset1(i, 0)
##########################################################################################################
# print 등의 메세지를 출력하는 방법
console(UART) # LN101 # (English) LM101 interface.

#######################################
# 실제 사용시에는 nTest = 0 으로 해야한다.
# (English) Set nTest = 0 when actually using. 
# 누르는 곳의 실제 좌표를 보고자 한다면 이 값을 1로 하고 터치를 하면 된다.
# (English) To see the actual coordinates, set this value as 1 and touch it.

nTest = 0  # 0 - Normal, 1 - 좌표출력 # (English) 0: Normal, 1 - Printing coordinates
nTest_BackgroundImage = 1 # test 시 표시될 페이지 # (English) Page displayed in test.
#######################################

# 테스트 모드가 아닌 경우만 초기자세 및 세팅등을 실행
# (English) Init pose and setting is executed only if it's not test mode.
if (nTest == 0):
    # controller direction : 0-vertical(Humanoid), 1-Horizontal
    eeprom.imu_type(0)
    #토크를 풀기전에 앉아준다.
    # (English) Sit down before Torque OFF.     
    Motion_Play_And_Wait(60)
    delay(100)
    # 토크를 Off 하고 액츄에이터의 설정 및 컨트롤러의 설정을 로봇에 맞게 수정한다.     
    # (English) Torque off, and modify DYNAMIXEL and controller configuration.    
    TorqAll(False)
    # profile -> velocity-based
    DXL(254).write8(10, 0) # 0 -> velocity-based profile, 4 -> time-based profile
    # Secondary ID(255: No Use, 0 ~ 252: ID)
    DXL(254).write8(12, 255) # 255 -> No Use(Clear)
    # Operation Mode(1:velocity[wheel], 3:position)    
    DXL(254).write8(11,3) # position
    TorqAll(True) 
    # 머리를 가운데로 움직여 둔다.
    # (English) Align the head a center.     
    OLLO(1, const.OLLO_JOINT_POSITION).write(512)
    
    # 모든 DXL의 속도를 초기상태로 되돌림
    # (English) Reset all DYNAMIXEL's velocity    
    Setup_Speed(254, 0)
    # 초기 자세
    # (English) Init pose    
    Motion_Ready(1)
    Offset_Read()
while(True) :
    HandleRosRemocon()
    if (IsPhone == False) :
        if (smart.is_connected() == True):
            #스마트폰과 연결되었는지 확인.
            # (English) Checking the connectivity with the smart device.            
            smart.wait_connected()
            #스마트폰 화면을 가로로 설정. (0:자동, 1:세로, 2:가로)
            # (English) Set the smart device from the portrait to the landscape screen.             
            smart.display.screen_orientation(2)
            #화면의 가로 세로를 가져오기 전에 화면이 전환되길 기다림.
            # (English) Wait for the screen convertion before bringing the screen's width and height.            
            delay(500)
            #동작하고 있는 카메라가 있다면 닫아준다.
            # (English) Close the camera if it's running
            #0:닫기, 1:색상, 2:얼굴감지, 3:스트리밍, 4:마커, 5:레인, 6:감정, 7:손 
            # (English) rpi.mode(0)#0: Close, 1:Color, 2: Facial Detection, 3:Streaming, 4: Marker, 5: Lane, 6: Emotion, 7: Hands             
            rpi.mode(0)
            smart.write8(10700, 0)
            #스마트폰 스트리밍 영상화면 0:닫기, 1:표시 
            # (English) Smart device's video streaming 0: Close, 1: Display
            #화면의 해상도를 가져와 CVar.nScreenWidth, CVar.nScreenHeight 에 넣어준다.
            # (English) Bringing the screen's resolution and add it to CVar.nScreenWidth and CVar.nScreenHeight.            
            GetResolution()
            # 배경 이미지를 출력
            # (English) Print the background image.            
            ShowPage(_PAGE_REMOTE_NORMAL)
            # 스마트폰이 연결 되었음을 변수에 기록
            # (English) Record to the variable that the smart device is successfully connected.            
            IsPhone = True
    else :
        # Test 1 => 좌표출력
        # (English) Test 1 => Coordinates print.         
        if (nTest == 1) :
            #스마트폰의 터치 입력을 확인
            # (English) Checking the input touch on the smart device.            
            GetTouch_Down()
            Test1(nTest_BackgroundImage)
        else:#Run
            #무릎의 굽어진 상태를 확인 - 100도 이상인 경우 낮은 자세 보행이 실행되도록 하기 위한 체크  
            # (English) Status check if the knee is down over 100 deg to execute low level posture walking.
            CheckKnee()
            # 버튼 눌림 체크
            # (English) Checking the button push            
            nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1 = GetButton(btnList)
            #메뉴바가 떠 있는 상태
            # (English) Menu bar is being displayed.            
            if (Event_Dn1 == 1):
                smart.etc.vibrate(10)
            elif (Event_Dn0 == 1):
                smart.etc.vibrate(10)
            if (CVar.nPage == _PAGE_MENU):
                Page_MenuBar(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1)
            else: #메뉴바가 떠있는 상태가 아닌 경우 # (English) If menu bar is not displayed.
                if (Btn0 == _BTN_MENU): # 메뉴버튼을 누르면 # (English) Clicking the menu button.
                    ShowPage(_PAGE_MENU) # 메뉴바를 띄운다. # (English) Display the menu bar.
                    WaitButtonUp()       # 버튼에서 손을 뗄 때까지 대기 # (English) Wait until hand-off out of the
                else:
                    if (
                        (CVar.nPage == _PAGE_REMOTE_NORMAL) or
                        (CVar.nPage == _PAGE_REMOTE_FIGHT) or
                        (CVar.nPage == _PAGE_REMOTE_SPECIAL) or
                        (CVar.nPage == _PAGE_STREAM)
                        ):
                        Page_Remote(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1)
                    elif (CVar.nPage == _PAGE_FACE_TRACK):
                        Page_Face_Track(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1)
                    elif (CVar.nPage == _PAGE_MOTOR_TEST):
                        Page_MotorTest(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1)
                    elif (CVar.nPage == _PAGE_OFFSET):
                        Page_Offset(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1)
                    elif (CVar.nPage == _PAGE_OFFSET_DIALOG1):
                        Page_Offset_Dialog_1(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1)
                    elif (CVar.nPage == _PAGE_OFFSET_DIALOG2):
                        Page_Offset_Dialog_2(nNum0, nNum1, Event_Dn0, Event_Dn1, Event_Up0, Event_Up1, Btn0, Btn1)
