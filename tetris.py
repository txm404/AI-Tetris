import pygame
import sys
import random
import os
from pygame import mixer

# 设置窗口居中
os.environ['SDL_VIDEO_CENTERED'] = '1'

# 初始化 Pygame
pygame.init()
mixer.init()  # 初始化音频系统

# 定义常量
SCREEN_WIDTH = 800  # 增加游戏窗口宽度，为预览区域留出空间
SCREEN_HEIGHT = 600  # 游戏窗口高度
BLOCK_SIZE = 30     # 方块大小
BOARD_WIDTH = 10    # 游戏区域宽度（以方块数为单位）
BOARD_HEIGHT = 20   # 游戏区域高度（以方块数为单位）
# 定义布局常量
BOARD_WIDTH_PX = BOARD_WIDTH * BLOCK_SIZE
PREVIEW_SIZE = 4 * BLOCK_SIZE
INFO_WIDTH_ESTIMATE = 150 # 信息区域估计宽度
GAP_INFO_BOARD = 50     # 信息区与游戏板间隙
GAP_BOARD_PREVIEW = 50  # 游戏板与预览区间隙

# 计算总内容宽度
total_content_width = INFO_WIDTH_ESTIMATE + GAP_INFO_BOARD + BOARD_WIDTH_PX + GAP_BOARD_PREVIEW + PREVIEW_SIZE

# 计算居中布局的起始 X 坐标
start_x = (SCREEN_WIDTH - total_content_width) // 2

# 设置动态计算的X坐标
INFO_X = start_x
BOARD_X = INFO_X + INFO_WIDTH_ESTIMATE + GAP_INFO_BOARD
PREVIEW_X = BOARD_X + BOARD_WIDTH_PX + GAP_BOARD_PREVIEW

# 设置游戏区域Y坐标 (垂直居中)
BOARD_Y = (SCREEN_HEIGHT - BOARD_HEIGHT * BLOCK_SIZE) // 2

# 设置预览区域Y坐标
PREVIEW_Y = BOARD_Y + 50

# 定义颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
BORDER_COLOR = (50, 50, 200)  # 游戏区域边框颜色
BG_COLOR = (20, 20, 40)  # 背景颜色

# 方块形状 (Tetrominoes) - 包含旋转
SHAPES = [
    # I
    [[[0,1,0,0], [0,1,0,0], [0,1,0,0], [0,1,0,0]], [[0,0,0,0], [1,1,1,1], [0,0,0,0], [0,0,0,0]]],
    # J
    [[[0,1,0], [0,1,0], [1,1,0]], [[1,0,0], [1,1,1], [0,0,0]], [[0,1,1], [0,1,0], [0,1,0]], [[0,0,0], [1,1,1], [0,0,1]]],
    # L
    [[[0,1,0], [0,1,0], [0,1,1]], [[0,0,0], [1,1,1], [1,0,0]], [[1,1,0], [0,1,0], [0,1,0]], [[0,0,1], [1,1,1], [0,0,0]]],
    # O
    [[[1,1], [1,1]]],
    # S
    [[[0,1,1], [1,1,0], [0,0,0]], [[0,1,0], [0,1,1], [0,0,1]]],
    # T
    [[[0,1,0], [1,1,1], [0,0,0]], [[0,1,0], [0,1,1], [0,1,0]], [[0,0,0], [1,1,1], [0,1,0]], [[0,1,0], [1,1,0], [0,1,0]]],
    # Z
    [[[1,1,0], [0,1,1], [0,0,0]], [[0,0,1], [0,1,1], [0,1,0]]]
]

# 方块颜色 - 主色和次色（用于渐变效果）
SHAPE_COLORS = [
    [(0, 255, 255), (0, 200, 200)],  # 青色 (Cyan)
    [(0, 0, 255), (0, 0, 200)],        # 蓝色 (Blue)
    [(255, 165, 0), (200, 130, 0)],    # 橙色 (Orange)
    [(255, 255, 0), (200, 200, 0)],    # 黄色 (Yellow)
    [(0, 255, 0), (0, 200, 0)],        # 绿色 (Green)
    [(128, 0, 128), (100, 0, 100)],    # 紫色 (Purple)
    [(255, 0, 0), (200, 0, 0)]         # 红色 (Red)
]

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('俄罗斯方块 - 增强版')

# 创建时钟对象，用于控制帧率
clock = pygame.time.Clock()

def create_board():
    """创建一个空的游戏板"""
    return [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

def is_valid_position(board, piece, offset_x=0, offset_y=0):
    """检查方块在给定位置是否有效（考虑偏移量）"""
    shape_index = piece['shape_index']
    rotation = piece['rotation'] % len(SHAPES[shape_index]) # 确保旋转索引有效
    shape = SHAPES[shape_index][rotation]

    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                try:
                    board_x = piece['x'] + x + offset_x
                    board_y = piece['y'] + y + offset_y

                    # 检查是否在游戏板内
                    if not (0 <= board_x < BOARD_WIDTH and 0 <= board_y < BOARD_HEIGHT):
                        return False
                    # 检查是否与现有方块碰撞 (board_y 必须非负)
                    if board_y < 0:
                        continue # 允许在顶部边界外开始，只要最终位置有效
                    if board[board_y][board_x] != 0:
                        return False
                except IndexError:
                    return False # 索引超出范围
    return True

def add_to_board(board, piece, effect_manager):
    """将落地的方块添加到游戏板上"""
    shape_index = piece['shape_index']
    rotation = piece['rotation'] % len(SHAPES[shape_index])
    shape = SHAPES[shape_index][rotation]
    color_index = piece['shape_index'] + 1 # 颜色索引从1开始，0代表空
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                board_y = piece['y'] + y
                board_x = piece['x'] + x
                # 确保添加到板上的位置在有效范围内
                if 0 <= board_y < BOARD_HEIGHT and 0 <= board_x < BOARD_WIDTH:
                    board[board_y][board_x] = color_index
                    # 添加闪光效果
                    effect_manager.add_flash(
                        BOARD_X + board_x * BLOCK_SIZE,
                        BOARD_Y + board_y * BLOCK_SIZE
                    )
    
    # 移除播放放置音效
    # play_sound('drop')

def clear_lines(board, effect_manager):
    """检查并清除满行，返回清除的行数"""
    lines_cleared = 0
    new_board = [row for row in board if any(cell == 0 for cell in row)]
    lines_cleared = BOARD_HEIGHT - len(new_board)
    
    # 在顶部添加新的空行
    for _ in range(lines_cleared):
        new_board.insert(0, [0 for _ in range(BOARD_WIDTH)])
    
    # 如果有行被清除，添加粒子效果
    if lines_cleared > 0:
        # play_sound('clear') # 移除播放音效
        # 为每行添加粒子爆炸效果
        for y in range(BOARD_HEIGHT - lines_cleared, BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                if board[y][x] != 0:
                    color = SHAPE_COLORS[board[y][x] - 1][0]
                    for _ in range(5):  # 每个方块生成5个粒子
                        effect_manager.add_particle(
                            BOARD_X + x * BLOCK_SIZE + BLOCK_SIZE//2,
                            BOARD_Y + y * BLOCK_SIZE + BLOCK_SIZE//2,
                            color,
                            (random.uniform(-2, 2), random.uniform(-2, 2)),
                            random.randint(20, 40)
                        )
    
    return new_board, lines_cleared

class EffectManager:
    """管理游戏中的各种特效"""
    def __init__(self):
        self.particles = []
        self.trails = []
        self.flashes = []
    
    def add_particle(self, x, y, color, velocity, lifetime):
        """添加粒子效果"""
        self.particles.append({
            'x': x, 'y': y, 'color': color,
            'velocity': velocity, 'lifetime': lifetime,
            'age': 0
        })
    
    def add_trail(self, x, y, color, alpha=200):
        """添加拖尾效果"""
        self.trails.append({
            'x': x, 'y': y, 'color': color,
            'alpha': alpha, 'size': BLOCK_SIZE
        })
    
    def add_flash(self, x, y, duration=10):
        """添加闪光效果"""
        self.flashes.append({
            'x': x, 'y': y, 'duration': duration,
            'timer': 0, 'alpha': 255
        })
    
    def update(self):
        """更新所有特效状态"""
        # 更新粒子
        for particle in self.particles[:]:
            particle['x'] += particle['velocity'][0]
            particle['y'] += particle['velocity'][1]
            particle['age'] += 1
            if particle['age'] >= particle['lifetime']:
                self.particles.remove(particle)
        
        # 更新拖尾
        for trail in self.trails[:]:
            trail['alpha'] -= 5
            trail['size'] -= 1
            if trail['alpha'] <= 0 or trail['size'] <= 0:
                self.trails.remove(trail)
        
        # 更新闪光
        for flash in self.flashes[:]:
            flash['timer'] += 1
            flash['alpha'] = 255 * (1 - flash['timer']/flash['duration'])
            if flash['timer'] >= flash['duration']:
                self.flashes.remove(flash)
    
    def draw(self, surface):
        """绘制所有特效"""
        # 绘制拖尾
        for trail in self.trails:
            alpha_surface = pygame.Surface((trail['size'], trail['size']), pygame.SRCALPHA)
            pygame.draw.rect(alpha_surface, (*trail['color'], trail['alpha']), 
                            (0, 0, trail['size'], trail['size']))
            surface.blit(alpha_surface, (trail['x'], trail['y']))
        
        # 绘制粒子
        for particle in self.particles:
            pygame.draw.circle(surface, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 2)
        
        # 绘制闪光
        for flash in self.flashes:
            flash_surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(flash_surface, (255, 255, 255, flash['alpha']), 
                            (0, 0, BLOCK_SIZE, BLOCK_SIZE))
            surface.blit(flash_surface, (flash['x'], flash['y']))

def draw_gradient_block(surface, rect, color1, color2, border_radius=3):
    """绘制带渐变效果的方块"""
    # 绘制主体方块（带圆角）
    pygame.draw.rect(surface, color1, rect, border_radius=border_radius)
    
    # 绘制高光效果
    highlight_rect = pygame.Rect(rect.left + 2, rect.top + 2, rect.width - 4, rect.height - 4)
    pygame.draw.rect(surface, color2, highlight_rect, border_radius=border_radius)
    
    # 绘制边框
    pygame.draw.rect(surface, BLACK, rect, 1, border_radius=border_radius)

def draw_board_border(surface):
    """绘制游戏区域边框"""
    border_rect = pygame.Rect(
        BOARD_X - 5, 
        BOARD_Y - 5, 
        BOARD_WIDTH * BLOCK_SIZE + 10, 
        BOARD_HEIGHT * BLOCK_SIZE + 10
    )
    pygame.draw.rect(surface, BORDER_COLOR, border_rect, 5, border_radius=10)

def draw_preview_border(surface):
    """绘制预览区域边框"""
    preview_rect = pygame.Rect(
        PREVIEW_X - 5, 
        PREVIEW_Y - 5, 
        PREVIEW_SIZE + 10, 
        PREVIEW_SIZE + 10
    )
    pygame.draw.rect(surface, BORDER_COLOR, preview_rect, 3, border_radius=8)
    draw_text(surface, "下一个", 30, PREVIEW_X + PREVIEW_SIZE // 2, PREVIEW_Y - 25, WHITE)

def draw_board(surface, board):
    """绘制游戏板背景和已固定的方块"""
    # 绘制游戏区域背景
    board_bg_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_WIDTH * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE)
    pygame.draw.rect(surface, BLACK, board_bg_rect)
    
    # 绘制网格线和已固定的方块
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            rect = pygame.Rect(BOARD_X + x * BLOCK_SIZE, BOARD_Y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            # 绘制已固定的方块
            if board[y][x] != 0:
                color_index = board[y][x] - 1 # 获取颜色索引
                color1 = SHAPE_COLORS[color_index][0]  # 主色
                color2 = SHAPE_COLORS[color_index][1]  # 次色
                draw_gradient_block(surface, rect, color1, color2)
            else:
                # 只绘制边框，不填充颜色
                pygame.draw.rect(surface, GRAY, rect, 1)

def new_piece():
    """生成一个新的随机方块"""
    shape_index = random.randint(0, len(SHAPES) - 1)
    piece = {
        'shape_index': shape_index,
        'rotation': 0,
        'x': BOARD_WIDTH // 2 - len(SHAPES[shape_index][0][0]) // 2, # 初始 x 位置居中
        'y': 0, # 初始 y 位置在顶部
        'color': SHAPE_COLORS[shape_index][0]  # 使用主色
    }
    return piece

def draw_piece(surface, piece, effect_manager, x_offset=0, y_offset=0, scale=1.0):
    """绘制方块，支持偏移和缩放（用于预览），并添加特效"""
    shape_index = piece['shape_index']
    rotation = piece['rotation'] % len(SHAPES[shape_index])
    shape = SHAPES[shape_index][rotation]
    color1 = SHAPE_COLORS[shape_index][0]  # 主色
    color2 = SHAPE_COLORS[shape_index][1]  # 次色
    
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                block_x = (BOARD_X + (piece['x'] + x) * BLOCK_SIZE) + x_offset
                block_y = (BOARD_Y + (piece['y'] + y) * BLOCK_SIZE) + y_offset
                rect = pygame.Rect(
                    block_x, 
                    block_y,
                    BLOCK_SIZE * scale, 
                    BLOCK_SIZE * scale
                )
                draw_gradient_block(surface, rect, color1, color2)
                
                # 添加拖尾效果
                effect_manager.add_trail(block_x, block_y, color1)

def draw_next_piece(surface, next_piece):
    """绘制下一个方块预览"""
    shape_index = next_piece['shape_index']
    rotation = next_piece['rotation'] % len(SHAPES[shape_index])
    shape = SHAPES[shape_index][rotation]
    color1 = SHAPE_COLORS[shape_index][0]  # 主色
    color2 = SHAPE_COLORS[shape_index][1]  # 次色
    
    # 计算预览方块的中心位置
    shape_width = len(shape[0]) * BLOCK_SIZE
    shape_height = len(shape) * BLOCK_SIZE
    center_x = PREVIEW_X + (PREVIEW_SIZE - shape_width) // 2
    center_y = PREVIEW_Y + (PREVIEW_SIZE - shape_height) // 2
    
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(
                    center_x + x * BLOCK_SIZE, 
                    center_y + y * BLOCK_SIZE, 
                    BLOCK_SIZE, 
                    BLOCK_SIZE
                )
                draw_gradient_block(surface, rect, color1, color2)

def draw_text(surface, text, size, x, y, color):
    """在指定位置绘制文本"""
    try:
        # 尝试使用支持中文的字体
        font = pygame.font.SysFont('SimHei', size) # 使用 'SimHei' 字体
    except pygame.error:
        # 如果 'SimHei' 不可用，使用默认字体
        print("警告：'SimHei' 字体不可用，将使用默认字体。中文可能无法正常显示。")
        font = pygame.font.Font(None, size) # 使用 Pygame 默认字体

    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)

def calculate_score(lines_cleared, level):
    """根据消除的行数和当前等级计算得分"""
    if lines_cleared == 0:
        return 0
    elif lines_cleared == 1:
        return 100 * level
    elif lines_cleared == 2:
        return 300 * level
    elif lines_cleared == 3:
        return 500 * level
    else:  # 4行（俄罗斯方块的最大可能值）
        return 800 * level

def calculate_level(total_lines):
    """根据总消除行数计算等级"""
    return total_lines // 10 + 1

def calculate_fall_speed(level):
    """根据等级计算下落速度"""
    return max(0.05, 0.5 - (level - 1) * 0.05)

def main():
    """游戏主函数"""
    # 初始化特效管理器
    effect_manager = EffectManager()
    
    board = create_board() # 初始化游戏板
    current_piece = new_piece() # 第一个方块
    next_piece = new_piece() # 下一个方块
    score = 0
    total_lines_cleared = 0
    level = 1
    game_over = False
    paused = False
    running = True

    fall_time = 0
    fall_speed = calculate_fall_speed(level) # 根据等级计算初始下落速度

    while running:
        dt = clock.tick(60) / 1000.0 # 获取自上一帧以来的时间（秒）
        
        # 更新特效
        effect_manager.update()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:  # 暂停/继续游戏
                    paused = not paused
                    # 移除暂停/恢复音效
                
                if not paused and not game_over:
                    if event.key == pygame.K_LEFT:
                        if is_valid_position(board, current_piece, offset_x=-1):
                            current_piece['x'] -= 1
                            # play_sound('move')
                    elif event.key == pygame.K_RIGHT:
                        if is_valid_position(board, current_piece, offset_x=1):
                            current_piece['x'] += 1
                            # play_sound('move')
                    elif event.key == pygame.K_DOWN:
                        if is_valid_position(board, current_piece, offset_y=1):
                            current_piece['y'] += 1
                            # play_sound('move')
                        else:
                            # 如果向下移动无效，则锁定方块
                            add_to_board(board, current_piece, effect_manager)
                            board, lines_cleared = clear_lines(board, effect_manager)
                            
                            # 更新分数和等级
                            total_lines_cleared += lines_cleared
                            old_level = level
                            level = calculate_level(total_lines_cleared)
                            score += calculate_score(lines_cleared, level)
                            
                            # 如果等级提升，更新下落速度
                            if level > old_level:
                                # play_sound('levelup') # 移除播放音效
                                fall_speed = calculate_fall_speed(level)
                            
                            # 更新当前方块和下一个方块
                            current_piece = next_piece
                            next_piece = new_piece()
                            
                            if not is_valid_position(board, current_piece):
                                game_over = True # 新方块无法放置，游戏结束
                                # play_sound('gameover') # 移除播放音效
                    elif event.key == pygame.K_UP: # 旋转
                        original_rotation = current_piece['rotation']
                        current_piece['rotation'] = (current_piece['rotation'] + 1) % len(SHAPES[current_piece['shape_index']])
                        if is_valid_position(board, current_piece):
                            # play_sound('rotate') # 移除播放音效
                            pass # 占位符，因为移除了 play_sound
                        else:
                            current_piece['rotation'] = original_rotation # 旋转无效，恢复原状
                    elif event.key == pygame.K_SPACE:  # 硬降（直接落到底部）
                        drop_distance = 0
                        while is_valid_position(board, current_piece, offset_y=drop_distance+1):
                            drop_distance += 1
                        current_piece['y'] += drop_distance
                        # 立即锁定方块
                        add_to_board(board, current_piece, effect_manager)
                        board, lines_cleared = clear_lines(board, effect_manager)
                        
                        # 更新分数和等级
                        total_lines_cleared += lines_cleared
                        old_level = level
                        level = calculate_level(total_lines_cleared)
                        score += calculate_score(lines_cleared, level)
                        
                        # 如果等级提升，更新下落速度
                        if level > old_level:
                            # play_sound('levelup') # 移除播放音效
                            fall_speed = calculate_fall_speed(level)
                        
                        # 更新当前方块和下一个方块
                        current_piece = next_piece
                        next_piece = new_piece()
                        
                        if not is_valid_position(board, current_piece):
                            game_over = True # 新方块无法放置，游戏结束
                            # play_sound('gameover') # 移除播放音效
                elif event.key == pygame.K_r and game_over: # 游戏结束后按 R 重启
                    board = create_board()
                    current_piece = new_piece()
                    next_piece = new_piece()
                    score = 0
                    total_lines_cleared = 0
                    level = 1
                    fall_speed = calculate_fall_speed(level)
                    game_over = False
                    paused = False

        if not paused and not game_over:
            # --- 游戏逻辑更新 ---
            # 方块自动下落
            fall_time += dt

            if fall_time >= fall_speed:
                fall_time = 0
                if is_valid_position(board, current_piece, offset_y=1):
                    current_piece['y'] += 1
                else:
                    # 无法向下移动，锁定方块
                    add_to_board(board, current_piece, effect_manager)
                    board, lines_cleared = clear_lines(board, effect_manager)
                    
                    # 更新分数和等级
                    total_lines_cleared += lines_cleared
                    old_level = level
                    level = calculate_level(total_lines_cleared)
                    score += calculate_score(lines_cleared, level)
                    
                    # 如果等级提升，更新下落速度
                    if level > old_level:
                        # play_sound('levelup') # 移除播放音效
                        fall_speed = calculate_fall_speed(level)
                    
                    # 更新当前方块和下一个方块
                    current_piece = next_piece
                    next_piece = new_piece()
                    
                    if not is_valid_position(board, current_piece):
                        game_over = True # 新方块无法放置，游戏结束
                        play_sound('gameover')

        # --- 绘制游戏界面 ---
        screen.fill(BG_COLOR) # 填充背景色
        
        # 绘制游戏区域边框
        draw_board_border(screen)
        
        # 绘制游戏板和固定方块
        draw_board(screen, board)
        
        # 绘制预览区域
        draw_preview_border(screen)
        draw_next_piece(screen, next_piece)
        
        # 绘制活动方块
        if not game_over and not paused:
            draw_piece(screen, current_piece, effect_manager)

        # 绘制分数和等级
        draw_text(screen, f"分数: {score}", 30, INFO_X, BOARD_Y + 50, WHITE)
        draw_text(screen, f"等级: {level}", 30, INFO_X, BOARD_Y + 100, WHITE)
        draw_text(screen, f"行数: {total_lines_cleared}", 30, INFO_X, BOARD_Y + 150, WHITE)
        
        # 绘制操作说明
        instructions = [
            "← → : 左右移动",
            "↑ : 旋转",
            "↓ : 加速下落",
            "空格 : 硬降",
            "P : 暂停/继续"
        ]
        for i, text in enumerate(instructions):
            draw_text(screen, text, 20, INFO_X, BOARD_Y + 200 + i * 30, WHITE)

        # 游戏暂停画面
        if paused and not game_over:
            # 半透明覆盖层
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # 黑色半透明
            screen.blit(overlay, (0, 0))
            
            draw_text(screen, "游戏暂停", 50, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30, WHITE)
            draw_text(screen, "按 P 继续", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, WHITE)

        # 游戏结束画面
        if game_over:
            # 半透明覆盖层
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # 黑色半透明
            screen.blit(overlay, (0, 0))
            
            draw_text(screen, "游戏结束", 50, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30, RED)
            draw_text(screen, f"最终分数: {score}", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, WHITE)
            draw_text(screen, "按 R 重新开始", 30, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60, WHITE)

        # 更新特效
        effect_manager.update()
        
        # 绘制特效
        effect_manager.draw(screen)
        
        # 更新显示
        pygame.display.flip()

    # 退出 Pygame
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()