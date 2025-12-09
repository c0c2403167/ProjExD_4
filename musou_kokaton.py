import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    x_diff, y_diff = dst.centerx - org.centerx, dst.centery - org.centery
    norm = math.sqrt(x_diff**2 + y_diff**2)
    # normが0に近い場合を保護
    if norm == 0:
        return 0.0, 0.0
    return x_diff / norm, y_diff / norm


class Bird(pg.sprite.Sprite):
    delta = {
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)
        self.imgs = {
            (+1, 0): img,
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),
            (-1, 0): img0,
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),
        }
         # --- 無敵（Hyper）用の画像 ---
        self.hyper_imgs = {k: pg.transform.laplacian(v) for k, v in self.imgs.items()}

         # --- 無敵（Hyper）用の画像 ---
        self.hyper_imgs = {k: pg.transform.laplacian(v) for k, v in self.imgs.items()}

        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal" # ←追加：状態(normal / hyper)
        self.hyper_life = 0 # ←追加：無敵の残りフレーム        self.state = "normal" # ←追加：状態(normal / hyper)
        self.hyper_life = 0 # ←追加：無敵の残りフレーム
    def change_img(self, num: int, screen: pg.Surface):
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed * sum_mv[0], self.speed * sum_mv[1])
        if key_lst[pg.K_LSHIFT]: #追加機能1
            self.speed = 20      
        else:
            self.speed = 10 
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)
        if self.state == "normal":
            self.image = self.imgs[self.dire]
        else:
            self.image = self.hyper_imgs[self.dire]
        screen.blit(self.image, self.rect)

class Bomb(pg.sprite.Sprite):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
              (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        super().__init__()
        rad = random.randint(10, 50)
        self.image = pg.Surface((2 * rad, 2 * rad))
        color = random.choice(__class__.colors)
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()

        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery + emy.rect.height // 2
        self.speed = 6

        self.inactive = False  # EMP 無効化状態

    def update(self):
        # inactive の場合は速度を半減して移動（仕様通り）
        if self.inactive:
            self.rect.move_ip((self.speed / 2) * self.vx, (self.speed / 2) * self.vy)
        else:
            self.rect.move_ip(self.speed * self.vx, self.speed * self.vy)

        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle: float = 0.0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        base_angle = math.degrees(math.atan2(-self.vy, self.vx))
        angle = base_angle + angle
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery + bird.rect.height * self.vy
        self.rect.centerx = bird.rect.centerx + bird.rect.width * self.vx
        self.speed = 10

    def update(self):
        self.rect.move_ip(self.speed * self.vx, self.speed * self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    def __init__(self, obj: "Bomb|Enemy", life: int):
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        self.life -= 1
        self.image = self.imgs[self.life // 10 % 2]
        if self.life < 0:
            self.kill()

class Gravity(pg.sprite.Sprite):
    """
    重力場に関するクラス
    画面全体を覆い、範囲内の爆弾を破壊する
    """
    def __init__(self, life: int):
        """
        重力場Surfaceを生成する
        引数 life：重力場の持続時間（フレーム数）
        """
        super().__init__()
        
        # 手順１：空のSurfaceインスタンスを生成する (画面全体)
        self.image = pg.Surface((WIDTH, HEIGHT))
        
        # 手順２：上記Surfaceにrectをdrawする (画面全体を黒で塗りつぶす)
        # 描画対象の矩形は、Surface全体(0, 0, WIDTH, HEIGHT)
        # Rectの引数は (左上x, 左上y, 幅, 高さ)
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, WIDTH, HEIGHT))  # 黒色 (0, 0, 0)
        
        # 手順３：上記Surfaceに透明度を設定する
        alpha = 150  # 透明度 (0:透明 ～ 255:不透明)
        self.image.set_alpha(alpha)
        
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)  # 画面左上隅に配置
        self.life = life

    def update(self):
        """
        発動時間を1減算し、0未満になったらkillする
        """
        self.life -= 1
        if self.life < 0:
            self.kill()


class Shield(pg.sprite.Sprite):
    """
    防御壁（青い矩形）
    - 幅20、高さはこうかとんの身長の2倍
    - life(発動時間)が0未満になったら消える
    - こうかとんの向きに合わせて回転し、前方に配置
    """
    def __init__(self, bird: Bird, life: int = 400):
        super().__init__()
        self.bird = bird
        self.life = life

        self.w = 20
        self.h = bird.rect.height * 2

        self.base_image = pg.Surface((self.w, self.h), pg.SRCALPHA)
        pg.draw.rect(self.base_image, (0, 0, 255), (0, 0, self.w, self.h))

        self.image = self.base_image
        self.rect = self.image.get_rect()
        self._refresh()  # 初期位置

    def _refresh(self):
        vx, vy = self.bird.dire  # 向き（-1,0,1）

        angle = math.degrees(math.atan2(-vy, vx))  # 角度 = degrees(atan2(-vy, vx))

        self.image = pg.transform.rotozoom(self.base_image, angle, 1.0) # 回転
        self.rect = self.image.get_rect()

        offset = max(self.bird.rect.width, self.bird.rect.height)  # 「こうかとん中心からこうかとん1体分」前にずらす
        self.rect.centerx = self.bird.rect.centerx + offset * vx
        self.rect.centery = self.bird.rect.centery + offset * vy

    def update(self):
        self.life -= 1
        self._refresh()
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]

    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT // 2)
        self.state = "down"
        self.interval = random.randint(50, 300)

        self.disabled = False  # EMP で無効化される

    def update(self):
        # disabled のときは停止処理（爆弾投下も interval を inf にしているのでここでは移動の制御のみ）
        if not self.disabled:
            if self.rect.centery > self.bound:
                self.vy = 0
                self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)
    
    


class Score:
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT - 50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class NeoBeam(pg.sprite.Sprite):
    """
    弾幕用クラス
    """
    
    def __init__(self, bird: Bird, num: int = 5):
        super().__init__()
        self.bird = bird
        self.num = num
        self.image = pg.Surface((1, 1), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=bird.rect.center)

    def gen_beams(self) -> list[Beam]:
        if self.num <= 1:
            angles = [0]
        else:
            if 100 % (self.num - 1) != 0:
                raise ValueError("num-1 must divide 100 to use range() step exactly")
            step = 100 // (self.num - 1)
            angles = list(range(-50, 51, step))

        return [Beam(self.bird, a) for a in angles]


class EMP:
    """EMP（電磁パルス）機能"""
    def __init__(self, emys: pg.sprite.Group, bombs: pg.sprite.Group, screen: pg.Surface):
        # --- 敵機の無力化 ---
        for emy in emys:
            emy.disabled = True
            emy.interval = float("inf")  # 爆弾を落とさなくする

            # --- ラプラシアン風フィルタ（NumPyなし） ---
            try:
                # Pygameの surfarray laplacian がある環境ではそちらを使用
                emy.image = pg.transform.laplacian(emy.image)
            except Exception:
                # 無い場合は疑似ラプラシアンを適用
                emy.image = self.fake_laplacian(emy.image)

            # rect を保つ
            emy.rect = emy.image.get_rect(center=emy.rect.center)

        # --- 爆弾の無力化 ---
        for bomb in bombs:
            bomb.inactive = True
            bomb.speed = max(1, bomb.speed / 2)

        # --- EMPフラッシュ ---
        surf = pg.Surface((WIDTH, HEIGHT))
        surf.set_alpha(120)
        surf.fill((255, 255, 0))
        screen.blit(surf, (0, 0))
        pg.display.update()
        time.sleep(0.05)

    def fake_laplacian(self, surf: pg.Surface) -> pg.Surface:
        w, h = surf.get_size()
        base = surf.copy()

        offset1 = pg.Surface((w, h), pg.SRCALPHA)
        offset2 = pg.Surface((w, h), pg.SRCALPHA)

        offset1.blit(surf, (-1, 0))   # 左へ
        offset2.blit(surf, (1, 0))    # 右へ

        base.blit(offset1, (0, 0), special_flags=pg.BLEND_RGB_SUB)
        base.blit(offset2, (0, 0), special_flags=pg.BLEND_RGB_SUB)

        # うっすら白を追加して「無力化」感を出す
        white = pg.Surface((w, h))
        white.fill((120, 120, 120))
        base.blit(white, (0, 0), special_flags=pg.BLEND_RGB_ADD)

        return base





def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    gravitys = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()

    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            # --- 無敵（Hyper）発動 ---
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT:
                if score.value >= 100 and bird.state == "normal":
                    bird.state = "hyper"
                    bird.hyper_life = 500
                    score.value -= 100

            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if key_lst[pg.K_LSHIFT]:
                    beams.add(NeoBeam(bird, num=5).gen_beams())
                else:
                    beams.add(Beam(bird))

            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                # 発動条件: リターンキー押下 and スコアが200より大 and 重力場が発動中でない
                if score.value >= 200 and len(gravitys) == 0:
                    gravitys.add(Gravity(400))  # 発動時間400フレームでインスタンス生成
                    score.value -= 200  # スコアを200消費

            if event.type == pg.KEYDOWN and event.key == pg.K_s:
                if score.value > 50 and len(shields) == 0:
                    shields.add(Shield(bird, 400))
                    score.value -= 50

            if event.type == pg.KEYDOWN and event.key == pg.K_e:
                score.value -= 20
                EMP(emys, bombs, screen)
            


        screen.blit(bg_img, [0, 0])

        if tmr % 200 == 0:
            emys.add(Enemy())

        # 敵機が停止状態で interval に応じて爆弾投下。ただし disabled (EMP) の敵は投下しない
        for emy in emys:
            if len(gravitys) > 0:# 重力場が発動中の場合のみ判定
            # 重力場と衝突した爆弾を処理（True, Falseで爆弾のみ削除）
                for bomb in pg.sprite.groupcollide(bombs, gravitys, True, False).keys(): # 重力場は削除しない(False)
                    exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                    score.value += 1 # 打ち落としたので1点アップ

            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():  # ビームと衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ
        
        hit_bombs = pg.sprite.spritecollide(bird, bombs, True)

        if bird.state == "hyper":
             for bomb in hit_bombs:
                 exps.add(Explosion(bomb, 50))
                 score.value += 1
        else:
            for bomb in hit_bombs:
                bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
        collided = pg.sprite.groupcollide(shields, bombs, False, True)
        for shield, bomb_list in collided.items():
            for bomb in bomb_list:
                exps.add(Explosion(bomb, 50))

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        # 更新・描画
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        shields.update()
        shields.draw(screen)
        gravitys.update()
        gravitys.draw(screen)
        exps.update()
        exps.draw(screen)
        # --- 無敵時間の減少 ---
        if bird.state == "hyper":
            bird.hyper_life -= 1
            if bird.hyper_life <= 0:
                bird.state = "normal"

        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    shields = pg.sprite.Group()
    pg.init()
    main()
    pg.quit()
    sys.exit()
