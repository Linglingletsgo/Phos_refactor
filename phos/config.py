from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class LayerConfig:
    """单个感光层的物理参数"""
    absorb_r: float = 0.0  # 吸收红光
    absorb_g: float = 0.0  # 吸收绿光
    absorb_b: float = 0.0  # 吸收蓝光
    scatter: float = 0.0   # 散射光比例 (d)
    direct: float = 1.0    # 直射光比例 (l)
    response: float = 1.0  # 响应系数 (x)
    grain: float = 0.0     # 颗粒度 (n)
    radius_mult: float = 1.0 # Multiplier for bloom radius (simulating wavelength scattering)

@dataclass
class CurveConfig:
    """胶片特性曲线参数 (ACES-like)"""
    gamma: float = 2.0
    A: float = 0.15  # 肩部强度
    B: float = 0.50  # 线性段强度
    C: float = 0.10  # 线性段平整度
    D: float = 0.20  # 趾部强度
    E: float = 0.02  # 趾部硬度
    F: float = 0.30  # 趾部软度

@dataclass
class FilmPreset:
    """完整的胶片预设配置"""
    name: str
    description: str
    type: str  # "color" or "soingle" (black & white)
    
    # 感光层配置
    red_layer: LayerConfig = field(default_factory=LayerConfig)
    green_layer: LayerConfig = field(default_factory=LayerConfig)
    blue_layer: LayerConfig = field(default_factory=LayerConfig)
    pan_layer: LayerConfig = field(default_factory=LayerConfig)  # 全色层 (用于黑白或总亮度)
    
    # 全局物理参数
    sens_factor: float = 1.0  # 高光敏感系数 (影响光晕)
    
    # 曲线配置
    curve: CurveConfig = field(default_factory=CurveConfig)

    # chemical crosstalk matrix (simulating dye coupling)
    # R depends on G, B densities etc.
    crosstalk: List[float] = field(default_factory=lambda: [
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0
    ])

# --- 预设定义 ---

NC200 = FilmPreset(
    name="NC200",
    description="Inspired by Fujifilm C200 & SP3000 scanner. Natural, soft, elegant.",
    type="color",
    sens_factor=0.5, # Reduced from 1.2
    # Red scatters most (radius_mult=1.5), Blue scatters least (0.7)
    red_layer=LayerConfig(0.77, 0.12, 0.18, scatter=0.20, direct=0.95, response=1.18, grain=0.18, radius_mult=1.5),
    green_layer=LayerConfig(0.08, 0.85, 0.23, scatter=0.15, direct=0.80, response=1.02, grain=0.18, radius_mult=1.0),
    blue_layer=LayerConfig(0.08, 0.09, 0.92, scatter=0.15, direct=0.88, response=0.78, grain=0.18, radius_mult=0.7),
    pan_layer=LayerConfig(0.25, 0.35, 0.35, grain=0.08), # Pan layer used for luminance calc
    curve=CurveConfig(gamma=2.05, A=0.15, B=0.50, C=0.10, D=0.20, E=0.02, F=0.30),
    # Slight coupling to simulating impure dyes
    crosstalk=[
        0.95, 0.05, 0.0,
        0.02, 0.96, 0.02,
        0.0,  0.05, 0.95
    ]
)

FS200 = FilmPreset(
    name="FS200",
    description="High contrast B&W positive 'Light'. Blue sensitive.",
    type="single",
    sens_factor=0.6,
    # Color absorption for B&W determines spectral sensitivity
    pan_layer=LayerConfig(0.15, 0.35, 0.45, scatter=0.3, direct=0.85, response=1.15, grain=0.20),
    curve=CurveConfig(gamma=2.2, A=0.15, B=0.50, C=0.10, D=0.20, E=0.02, F=0.30)
)

AS100 = FilmPreset(
    name="AS100 (B&W)",
    description="Inspired by Fujifilm ACROS 100. High sharpness, rich tonal gradation.",
    type="single",
    sens_factor=1.0,
    # Pan layer sensitivity (orthopanchromatic - less red sensitivity)
    pan_layer=LayerConfig(0.28, 0.40, 0.32, direct=0.7, scatter=0.2, grain=0.10, radius_mult=1.0),
    curve=CurveConfig(gamma=2.2, A=0.25, B=0.40, C=0.15, D=0.25, E=0.01, F=0.30)
)

# --- Calibrated Presets (Datasheet Based) ---

PORTRA_400 = FilmPreset(
    name="Kodak Portra 400",
    description="Professional Color Negative. Exceptional skin tones, fine grain, high latitude.",
    type="color",
    sens_factor=0.6,
    # Red Layer (Cyan Dye): Slight secondary peak in Blue (makes shadows cooler/cyanish if uncorrected, but scanner corrects this)
    # Visual result: Warm, natural skin.
    red_layer=LayerConfig(0.75, 0.15, 0.10, scatter=0.22, radius_mult=1.6), 
    green_layer=LayerConfig(0.10, 0.80, 0.10, scatter=0.18, radius_mult=1.1),
    blue_layer=LayerConfig(0.05, 0.10, 0.85, scatter=0.18, radius_mult=0.8),
    
    # Very gentle curve (High Latitude)
    curve=CurveConfig(gamma=1.8, A=0.10, B=0.60, C=0.08, D=0.30, E=0.05, F=0.40),
    
    # Crosstalk: 
    # Cyan dye (from Red) has absorption in Green and Blue.
    # Magenta dye (from Green) has absorption in Blue.
    crosstalk=[
        0.96, 0.02, 0.0,
        0.04, 0.94, 0.02, # Yellow/Red pollution in Green
        0.08, 0.08, 0.90  # Stronger absorption of Blue by Cyan/Mag dyes -> Yellowish cast (Classic Kodak Warmth)
    ]
)

FUJI_400H = FilmPreset(
    name="Fujifilm Pro 400H",
    description="Professional Color Negative. '4th Color Layer' technology. Cool shadows, faithful colors.",
    type="color",
    sens_factor=0.6,
    
    # Fuji characteristics: 
    # Green layer is very sharp. 
    # "4th Layer" implies complex spectral mapping, simplified here as broader Cyan sensitivity.
    red_layer=LayerConfig(0.70, 0.20, 0.10, scatter=0.20, radius_mult=1.5),
    green_layer=LayerConfig(0.05, 0.85, 0.10, scatter=0.15, radius_mult=1.0), # Pure Green
    blue_layer=LayerConfig(0.10, 0.10, 0.80, scatter=0.25, radius_mult=0.9), # Scatters more than usual
    
    # Slightly punchier contrast in midtones, lifting shadows
    curve=CurveConfig(gamma=1.9, A=0.18, B=0.55, C=0.12, D=0.25, E=0.01, F=0.35),
    
    crosstalk=[
        0.94, 0.06, 0.0,
        0.00, 0.98, 0.02, # Very clean Magenta dye
        0.02, 0.05, 0.93  # Cleaner Blue channel than Kodak
    ]
)

TRI_X_400 = FilmPreset(
    name="Kodak Tri-X 400",
    description="The Photojournalism Standard (1954). High contrast, gritty grain, dramatic.",
    type="single",
    sens_factor=1.0,
    # Blue sensitive (classic emulsion) -> darker reds
    pan_layer=LayerConfig(0.25, 0.35, 0.40, direct=0.6, scatter=0.25, grain=0.15, radius_mult=1.0),
    curve=CurveConfig(gamma=2.4, A=0.30, B=0.35, C=0.20, D=0.20, E=0.01, F=0.25)
)

KODACHROME_64 = FilmPreset(
    name="Kodachrome 64",
    description="The Legend (1974). Color Reversal Film. Deep blacks, vivid reds, sharp.",
    type="color",
    sens_factor=0.3, # Slower film
    # Reversal characteristics: High contrast, high saturation (via purity)
    # Red is dominant and dense
    red_layer=LayerConfig(0.85, 0.05, 0.05, scatter=0.15, direct=1.2, radius_mult=1.1),
    green_layer=LayerConfig(0.05, 0.85, 0.10, scatter=0.10, direct=1.1, radius_mult=1.0),
    blue_layer=LayerConfig(0.05, 0.10, 0.85, scatter=0.10, direct=1.1, radius_mult=0.9),
    
    # High Gamma for Slide Film
    curve=CurveConfig(gamma=2.4, A=0.35, B=0.20, C=0.20, D=0.15, E=0.00, F=0.20),
    
    # Very pure dyes, little crosstalk compared to negatives
    crosstalk=[
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0
    ]
)

VISION3_250D = FilmPreset(
    name="Kodak Vision3 250D",
    description="Modern Hollywood Standard (5207). Neutral, extreme latitude, red halation.",
    type="color",
    sens_factor=0.7,
    # REMJET removed? Phos simulates the look with it removed but halation remaining
    # Strong Red Halation
    red_layer=LayerConfig(0.70, 0.20, 0.10, scatter=0.30, direct=1.0, radius_mult=1.8),
    green_layer=LayerConfig(0.10, 0.80, 0.10, scatter=0.20, direct=1.0, radius_mult=1.2),
    blue_layer=LayerConfig(0.10, 0.10, 0.80, scatter=0.20, direct=1.0, radius_mult=0.8),
    
    # ACES-like curve implicitly desired, but here specific mapping
    curve=CurveConfig(gamma=1.7, A=0.10, B=0.70, C=0.05, D=0.40, E=0.06, F=0.50),
    
    crosstalk=[
        0.95, 0.05, 0.0,
        0.05, 0.90, 0.05,
        0.0,  0.05, 0.95
    ]
)

PRESETS: Dict[str, FilmPreset] = {
    "Kodak Portra 400": PORTRA_400,
    "Fuji Pro 400H": FUJI_400H,
    "Kodak Tri-X 400": TRI_X_400,
    "Kodachrome 64": KODACHROME_64,
    "Kodak Vision3 250D": VISION3_250D,
    "NC200": NC200,
    "FS200": FS200,
    "AS100": AS100,
}

def get_preset(name: str) -> FilmPreset:
    return PRESETS.get(name, NC200)
