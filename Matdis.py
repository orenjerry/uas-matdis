import pygame
import random
import sys
import math

# KONFIGURASI
LEBAR_LAYAR, TINGGI_LAYAR = 900, 900
WARNA_ASPAL = (50, 50, 50)
WARNA_GARIS = (255, 255, 255)
WARNA_KUNING = (255, 215, 0)
WARNA_RUMPUT = (34, 139, 34)

# Warna Mobil
MOBIL_LURUS = (0, 100, 255)     # Biru
MOBIL_KANAN = (255, 100, 0)     # Oranye
MOBIL_KIRI  = (0, 255, 255)     # Cyan

# Warna Lampu
MERAH = (255, 0, 0)
KUNING = (255, 255, 0)
HIJAU = (0, 255, 0)
ABU_MATI = (60, 60, 60)

# Geometri
CX, CY = LEBAR_LAYAR // 2, TINGGI_LAYAR // 2
LEBAR_PER_LAJUR = 40
LEBAR_TOTAL_JALAN = LEBAR_PER_LAJUR * 4 
BATAS_BOX = LEBAR_TOTAL_JALAN // 2 

JARAK_AMAN = 50
DURASI_HIJAU = 300   
DURASI_KUNING = 90  
DURASI_JEDA = 60     

pygame.init()
layar = pygame.display.set_mode((LEBAR_LAYAR, TINGGI_LAYAR))
pygame.display.set_caption("Simulasi Simpang: Belokan Realistis (Maju Dulu)")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 14, bold=True)

class Mobil:
    def __init__(self, asal):
        self.asal = asal
        self.ukuran = 22
        self.kecepatan_maks = 4
        self.kecepatan = self.kecepatan_maks
        self.selesai = False
        self.lewat_stop_line = False
        
        # Status Belok
        self.sedang_belok = False
        self.jalur_belok = [] 
        self.index_belok = 0
        
        rand = random.random()
        if rand < 0.60:
            self.arah_tujuan = 'LURUS'
            self.lajur = 1 
        else:
            self.arah_tujuan = 'KANAN' 
            self.lajur = 1 

        self.offset_start = LEBAR_PER_LAJUR * 1.5 if self.lajur == 0 else LEBAR_PER_LAJUR * 0.5

        if asal == 'A': # Bawah
            self.x = CX - self.offset_start
            self.y = TINGGI_LAYAR + 20
            self.dx, self.dy = 0, -1
        elif asal == 'B': # Kanan
            self.x = LEBAR_LAYAR + 20
            self.y = CY + self.offset_start
            self.dx, self.dy = -1, 0
        elif asal == 'C': # Atas
            self.x = CX + self.offset_start
            self.y = -20
            self.dx, self.dy = 0, 1
        elif asal == 'D': # Kiri
            self.x = -20
            self.y = CY - self.offset_start
            self.dx, self.dy = 1, 0

    def hitung_kurva_bezier(self, p0, p1, p2, langkah=30):
        jalur = []
        for t in range(langkah + 1):
            t /= langkah
            x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
            y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
            jalur.append((x, y))
        return jalur

    def inisialisasi_belok(self):
        if self.arah_tujuan != 'KANAN':
            return

        p0 = (self.x, self.y)
        p1 = (CX, CY) # Default Center
        p2 = (0, 0) 
        
        # offset_target_luar = LEBAR_PER_LAJUR * 1.5 
        offset_target_dalam = LEBAR_PER_LAJUR * 0.5 

        # Logika Belok Kanan
        if self.arah_tujuan == 'KANAN':
            deep_factor = 30
            
            if self.asal == 'A': # Bawah -> Kanan (Timur)
                p1 = (CX + deep_factor, CY - deep_factor) 
                # tujuan: lajur kiri arah timur (y lebih kecil)
                p2 = (CX + BATAS_BOX + 100, CY - offset_target_dalam) 
            
            elif self.asal == 'B': # Kanan -> Kanan (Utara)
                p1 = (CX - deep_factor, CY - deep_factor)
                # tujuan: lajur kiri arah utara (x lebih kecil)
                p2 = (CX - offset_target_dalam, CY - BATAS_BOX - 100) 
            
            elif self.asal == 'C': # Atas -> Kanan (Barat)
                p1 = (CX - deep_factor, CY + deep_factor)
                # tujuan: lajur kiri arah barat (y lebih besar)
                p2 = (CX - BATAS_BOX - 100, CY + offset_target_dalam)
            
            elif self.asal == 'D': # Kiri -> Kanan (Selatan)
                p1 = (CX + deep_factor, CY + deep_factor)
                # tujuan: lajur kiri arah selatan (x lebih besar)
                p2 = (CX + offset_target_dalam, CY + BATAS_BOX + 100)
            
            steps = 30

        self.jalur_belok = self.hitung_kurva_bezier(p0, p1, p2, steps)
        self.sedang_belok = True

    def cek_depan(self, semua_mobil):
        for m in semua_mobil:
            if m is self or m.selesai: continue
            if not self.sedang_belok and not m.sedang_belok:
                if m.asal == self.asal and m.lajur == self.lajur:
                    dist = math.sqrt((self.x - m.x)**2 + (self.y - m.y)**2)
                    if self.asal == 'A' and m.y < self.y and dist < JARAK_AMAN: return True
                    if self.asal == 'B' and m.x < self.x and dist < JARAK_AMAN: return True
                    if self.asal == 'C' and m.y > self.y and dist < JARAK_AMAN: return True
                    if self.asal == 'D' and m.x > self.x and dist < JARAK_AMAN: return True
        return False

    def gerak(self, lampu_status, semua_mobil):
        margin_stop = BATAS_BOX + 3
        jarak_ke_stop = 0
        
        if self.asal == 'A': jarak_ke_stop = self.y - (CY + margin_stop)
        elif self.asal == 'B': jarak_ke_stop = self.x - (CX + margin_stop)
        elif self.asal == 'C': jarak_ke_stop = (CY - margin_stop) - self.y
        elif self.asal == 'D': jarak_ke_stop = (CX - margin_stop) - self.x
        
        # Logika Lewat Stop Line
        if jarak_ke_stop < 5: self.lewat_stop_line = True

        stop = False
        if not self.lewat_stop_line:
            if 0 < jarak_ke_stop < 100:
                if lampu_status in ['MERAH', 'MERAH_TRANSISI']: stop = True
                elif lampu_status == 'KUNING' and jarak_ke_stop < 40: stop = True

        if stop or self.cek_depan(semua_mobil):
            self.kecepatan = 0
        else:
            if self.kecepatan < self.kecepatan_maks: self.kecepatan += 0.2
            if self.arah_tujuan != 'LURUS' and 0 < jarak_ke_stop < 80:
                self.kecepatan = min(self.kecepatan, 2.5)

        # Movement
        if self.sedang_belok:
            if self.index_belok < len(self.jalur_belok):
                tx, ty = self.jalur_belok[self.index_belok]
                dx, dy = tx - self.x, ty - self.y
                dist = math.sqrt(dx**2 + dy**2)
                
                if dist > 0:
                    self.x += (dx / dist) * self.kecepatan
                    self.y += (dy / dist) * self.kecepatan
                
                if dist < self.kecepatan + 2:
                    self.index_belok += 1
            else:
                if self.jalur_belok:
                    self.x, self.y = self.jalur_belok[-1]

                if self.asal == 'A':
                    self.dx = 1; self.dy = 0
                elif self.asal == 'B':
                    self.dx = 0; self.dy = -1
                elif self.asal == 'C':
                    self.dx = -1; self.dy = 0
                elif self.asal == 'D':
                    self.dx = 0; self.dy = 1
                
                self.sedang_belok = False 
                self.x += self.dx * self.kecepatan
                self.y += self.dy * self.kecepatan

        else:
            # Gerak Lurus
            self.x += self.dx * self.kecepatan
            self.y += self.dy * self.kecepatan

            # Trigger Logic
            if not self.sedang_belok and self.arah_tujuan == 'KANAN' and self.lewat_stop_line:
                
                # Hitung jarak dari mobil ke Titik Tengah Persimpangan
                dist_center = math.sqrt((self.x - CX)**2 + (self.y - CY)**2)
                
                # BELOK KANAN: Tunggu sampai DEKAT SEKALI dengan tengah
                if dist_center < 25:
                    self.inisialisasi_belok()

        if not (-50 <= self.x <= LEBAR_LAYAR + 50) or not (-50 <= self.y <= TINGGI_LAYAR + 50):
            self.selesai = True

    def gambar(self, surface):
        if self.arah_tujuan == 'LURUS': warna = MOBIL_LURUS
        elif self.arah_tujuan == 'KANAN': warna = MOBIL_KANAN
        else: warna = MOBIL_KIRI

        pygame.draw.rect(surface, warna, (self.x - 10, self.y - 10, 20, 20), border_radius=5)
        if self.arah_tujuan != 'LURUS':
            if pygame.time.get_ticks() % 500 < 250:
                pygame.draw.circle(surface, (255, 255, 200), (int(self.x), int(self.y)), 4)
        if self.kecepatan < 0.2:
            pygame.draw.circle(surface, MERAH, (int(self.x), int(self.y)), 5)

def gambar_jalan(surface):
    surface.fill(WARNA_RUMPUT)
    pygame.draw.rect(surface, WARNA_ASPAL, (CX - BATAS_BOX, 0, LEBAR_TOTAL_JALAN, TINGGI_LAYAR))
    pygame.draw.rect(surface, WARNA_ASPAL, (0, CY - BATAS_BOX, LEBAR_LAYAR, LEBAR_TOTAL_JALAN))
    
    # Marka Jalan
    pygame.draw.line(surface, WARNA_KUNING, (CX-2, 0), (CX-2, CY - BATAS_BOX), 2)
    pygame.draw.line(surface, WARNA_KUNING, (CX+2, 0), (CX+2, CY - BATAS_BOX), 2)
    pygame.draw.line(surface, WARNA_KUNING, (CX-2, CY + BATAS_BOX), (CX-2, TINGGI_LAYAR), 2)
    pygame.draw.line(surface, WARNA_KUNING, (CX+2, CY + BATAS_BOX), (CX+2, TINGGI_LAYAR), 2)
    pygame.draw.line(surface, WARNA_KUNING, (0, CY-2), (CX - BATAS_BOX, CY-2), 2)
    pygame.draw.line(surface, WARNA_KUNING, (0, CY+2), (CX - BATAS_BOX, CY+2), 2)
    pygame.draw.line(surface, WARNA_KUNING, (CX + BATAS_BOX, CY-2), (LEBAR_LAYAR, CY-2), 2)
    pygame.draw.line(surface, WARNA_KUNING, (CX + BATAS_BOX, CY+2), (LEBAR_LAYAR, CY+2), 2)

    dash, gap = 20, 20
    for y in range(0, int(CY - BATAS_BOX), dash + gap):
        pygame.draw.line(surface, WARNA_GARIS, (CX - LEBAR_PER_LAJUR, y), (CX - LEBAR_PER_LAJUR, y+dash), 1)
        pygame.draw.line(surface, WARNA_GARIS, (CX + LEBAR_PER_LAJUR, y), (CX + LEBAR_PER_LAJUR, y+dash), 1)
    for y in range(int(CY + BATAS_BOX), TINGGI_LAYAR, dash + gap):
        pygame.draw.line(surface, WARNA_GARIS, (CX - LEBAR_PER_LAJUR, y), (CX - LEBAR_PER_LAJUR, y+dash), 1)
        pygame.draw.line(surface, WARNA_GARIS, (CX + LEBAR_PER_LAJUR, y), (CX + LEBAR_PER_LAJUR, y+dash), 1)
    for x in range(0, int(CX - BATAS_BOX), dash + gap):
        pygame.draw.line(surface, WARNA_GARIS, (x, CY - LEBAR_PER_LAJUR), (x+dash, CY - LEBAR_PER_LAJUR), 1)
        pygame.draw.line(surface, WARNA_GARIS, (x, CY + LEBAR_PER_LAJUR), (x+dash, CY + LEBAR_PER_LAJUR), 1)
    for x in range(int(CX + BATAS_BOX), LEBAR_LAYAR, dash + gap):
        pygame.draw.line(surface, WARNA_GARIS, (x, CY - LEBAR_PER_LAJUR), (x+dash, CY - LEBAR_PER_LAJUR), 1)
        pygame.draw.line(surface, WARNA_GARIS, (x, CY + LEBAR_PER_LAJUR), (x+dash, CY + LEBAR_PER_LAJUR), 1)

    # Garis Stop Solid
    tebal = 6
    pygame.draw.line(surface, WARNA_GARIS, (CX - BATAS_BOX, CY + BATAS_BOX), (CX, CY + BATAS_BOX), tebal)
    pygame.draw.line(surface, WARNA_GARIS, (CX, CY - BATAS_BOX), (CX + BATAS_BOX, CY - BATAS_BOX), tebal)
    pygame.draw.line(surface, WARNA_GARIS, (CX - BATAS_BOX, CY - BATAS_BOX), (CX - BATAS_BOX, CY), tebal)
    pygame.draw.line(surface, WARNA_GARIS, (CX + BATAS_BOX, CY), (CX + BATAS_BOX, CY + BATAS_BOX), tebal)

def gambar_lampu(surface, pos, status, label):
    x, y = pos
    pygame.draw.rect(surface, (20,20,20), (x, y, 40, 100), border_radius=8)
    m, k, h = ABU_MATI, ABU_MATI, ABU_MATI
    if status in ['MERAH', 'MERAH_TRANSISI']: m = MERAH
    elif status == 'KUNING': k = KUNING
    elif status == 'HIJAU': h = HIJAU
    pygame.draw.circle(surface, m, (x+20, y+20), 12)
    pygame.draw.circle(surface, k, (x+20, y+50), 12)
    pygame.draw.circle(surface, h, (x+20, y+80), 12)
    teks = font.render(label, True, (255, 255, 255))
    surface.blit(teks, (x + 10, y - 20))

def main():
    list_mobil = []
    urutan_fase = ['A', 'B', 'C', 'D']
    fase_aktif = 0 
    timer = DURASI_HIJAU
    status_lampu = 'HIJAU' 
    spawn_timer = 0 

    running = True
    while running:
        layar.fill((0,0,0))
        gambar_jalan(layar)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        timer -= 1
        if timer <= 0:
            if status_lampu == 'HIJAU': status_lampu = 'KUNING'; timer = DURASI_KUNING
            elif status_lampu == 'KUNING': status_lampu = 'MERAH_TRANSISI'; timer = DURASI_JEDA
            elif status_lampu == 'MERAH_TRANSISI': status_lampu = 'HIJAU'; timer = DURASI_HIJAU; fase_aktif = (fase_aktif + 1) % 4 

        status_per_jalan = {'A': 'MERAH', 'B': 'MERAH', 'C': 'MERAH', 'D': 'MERAH'}
        if status_lampu != 'MERAH_TRANSISI': status_per_jalan[urutan_fase[fase_aktif]] = status_lampu

        spawn_timer += 1
        if spawn_timer > 25: 
            if random.randint(1, 10) > 3: 
                asal = random.choice(['A', 'B', 'C', 'D'])
                mobil_baru = Mobil(asal)
                aman = True
                for m in list_mobil:
                    if m.asal == mobil_baru.asal and m.lajur == mobil_baru.lajur:
                        dist = math.sqrt((m.x - mobil_baru.x)**2 + (m.y - mobil_baru.y)**2)
                        if dist < 50: aman = False; break
                if aman: list_mobil.append(mobil_baru)
            spawn_timer = 0

        for mobil in list_mobil[:]:
            status_saat_ini = status_per_jalan.get(mobil.asal, 'HIJAU')
            mobil.gerak(status_saat_ini, list_mobil)
            mobil.gambar(layar)
            if mobil.selesai: list_mobil.remove(mobil)

        offset_lampu = BATAS_BOX + 20
        gambar_lampu(layar, (CX - offset_lampu - 60, CY + offset_lampu), status_per_jalan['A'], "A")
        gambar_lampu(layar, (CX + offset_lampu + 20, CY + offset_lampu), status_per_jalan['B'], "B")
        gambar_lampu(layar, (CX + offset_lampu + 20, CY - offset_lampu - 100), status_per_jalan['C'], "C")
        gambar_lampu(layar, (CX - offset_lampu - 60, CY - offset_lampu - 100), status_per_jalan['D'], "D")

        info = f"FASE: {urutan_fase[fase_aktif]} | LAMPU: {status_lampu}"
        layar.blit(font.render(info, True, (255,255,255), (0,0,0)), (10, 10))
        pygame.display.flip(); clock.tick(60)

    pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()