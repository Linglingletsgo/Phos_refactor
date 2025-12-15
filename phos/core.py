import cv2
import numpy as np
from typing import Tuple, Optional, List
from .config import FilmPreset, CurveConfig

def standardize(image: np.ndarray, min_size: int = 3000) -> np.ndarray:
    """标准化图像尺寸"""
    height, width = image.shape[:2]
    
    if height < width:
        scale_factor = min_size / height
        new_height = min_size
        new_width = int(width * scale_factor)
    else:
        scale_factor = min_size / width
        new_width = min_size
        new_height = int(height * scale_factor)
    
    # Ensure even dimensions
    new_width = new_width + 1 if new_width % 2 != 0 else new_width
    new_height = new_height + 1 if new_height % 2 != 0 else new_height
    
    interpolation = cv2.INTER_AREA if scale_factor < 1 else cv2.INTER_LANCZOS4
    return cv2.resize(image, (new_width, new_height), interpolation=interpolation)

class GaussianPyramid:
    @staticmethod
    def render_bloom(img: np.ndarray, strength: float, radius_mult: float = 1.0, levels: int = 6) -> np.ndarray:
        """
        使用金字塔算法计算物理光晕 (Physical Bloom).
        通过叠加不同尺度的模糊层来模拟光线在复杂介质（如镜头、胶片片基）中的散射。
        
        Args:
            img: 线性光照图像 (float32)
            strength: 光晕强度
            radius_mult: 半径乘数 (Red > 1.0, Blue < 1.0)
            levels: 金字塔层数
        """
        if strength <= 0:
            return np.zeros_like(img)

        # 1. Downsample
        pyramid = [img]
        current = img
        for _ in range(levels):
            # PyrDown uses Gaussian blur then removes even rows/cols
            current = cv2.pyrDown(current)
            pyramid.append(current)
            
        # 2. Upsample and Accumulate
        bloom_accum = np.zeros_like(img)
        
        # Base weights
        layer_weights = np.array([0.0, 0.1, 0.2, 0.4, 0.8, 1.0, 1.0])
        
        # Adjust weights based on radius_mult
        # If radius_mult > 1 (Red), we want more contribution from higher levels.
        # Simple heuristic: shift indices effectively?
        # Better: scale the index access or modulate weights.
        
        # Let's apply a "center of mass" shift to the weights
        # If radius_mult is 1.5, we favor upper levels.
        # This is surprisingly tricky to map linearly.
        
        # Alternative: Just modulate the weights by a power function based on level index?
        # weight[i] *= (i * radius_mult) ?
        
        for i in range(1, len(pyramid)):
            base_w = layer_weights[i] if i < len(layer_weights) else 1.0
            
            # Modifier:
            # i=1 is small scale details. i=6 is large halo.
            # R (radius_mult > 1): boost large scales (i large).
            # B (radius_mult < 1): attenuate large scales.
            
            # Empirically:
            modifier = np.power(i, radius_mult - 1.0) # If mult=1, mod=1. If mult=2, mod=i.
            # Wait, this might explode weights.
            
            # Let's use a smoother shift.
            # Interpret radius_mult as scaling the "effective level".
            # But we only have discrete levels.
            
            # Let's stick to a simpler tweak:
            # Just multiply the weight by radius_mult for higher levels?
            # Or use a power curve for the envelope?
            
            # Let's try: w_new = w * (radius_mult ** (i/2))
            # i=2, mult=1.5 -> w * 1.5. 
            # i=4, mult=1.5 -> w * 2.25.
            # Boosts large halos significantly for Red.
            
            w = base_w * (radius_mult ** (i * 0.5))
            
            layer = pyramid[i]
            layer_upscaled = cv2.resize(layer, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
            
            bloom_accum += layer_upscaled * w
            
        # Normalize slightly to prevent massive energy addition
        # If we boosted weights, we boosted energy. 
        # But halation IS energy boost in specific areas? No, energy conservation implies scattering just moves light.
        # So we should normalize the kernel sum? 
        # For simplicity in this art-directed sim, we just scale by typical strength.
        bloom_accum = bloom_accum * (strength * 0.1) 
        
        return bloom_accum

class FilmRenderer:
    def __init__(self, preset: FilmPreset):
        self.preset = preset

    def _to_linear_float(self, image: np.ndarray) -> np.ndarray:
        """Convert input to Linear Float32."""
        if image.dtype == np.uint8:
            # Assume sRGB input -> Linearize (Approx Gamma 2.2)
            img_float = image.astype(np.float32) / 255.0
            return np.power(img_float, 2.2)
        elif image.dtype == np.uint16:
            # Assume Linear 16-bit (from Raw loader)
            return image.astype(np.float32) / 65535.0
        else:
            # Assume already float
            return image.astype(np.float32)

    def _calculate_luminance(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray], np.ndarray]:
        """计算各感光层的线性受光量"""
        # Image is already (B, G, R) float32
        b, g, r = cv2.split(image)
        
        p = self.preset
        
        # Calculate Total Luminance (Pan layer)
        lux_total = (p.pan_layer.absorb_r * r + 
                     p.pan_layer.absorb_g * g + 
                     p.pan_layer.absorb_b * b)

        if p.type == "color":
            # Color film layers response
            lux_r = (p.red_layer.absorb_r * r + 
                     p.red_layer.absorb_g * g + 
                     p.red_layer.absorb_b * b)
            lux_g = (p.green_layer.absorb_r * r + 
                     p.green_layer.absorb_g * g + 
                     p.green_layer.absorb_b * b)
            lux_b = (p.blue_layer.absorb_r * r + 
                     p.blue_layer.absorb_g * g + 
                     p.blue_layer.absorb_b * b)
            return lux_r, lux_g, lux_b, lux_total
        else:
            return None, None, None, lux_total

    def _apply_grain(self, channel: np.ndarray, base_grain: float, sens: np.ndarray, iso: int) -> np.ndarray:
        """
        应用颗粒 (Granularity) based on ISO.
        ISO 100 is baseline.
        """
        if iso <= 0:
            return np.zeros_like(channel)

        # ISO formula: higher ISO = stronger, larger grain
        # Let's approximate: 
        # Grain strength ~ sqrt(ISO)
        iso_factor = (iso / 200.0) ** 0.6  # Tuned curve
        
        real_grain_size = base_grain * iso_factor
        
        # Fast noise generation
        noise = np.random.normal(0, 1, channel.shape).astype(np.float32)
        
        # Grain visibility weights (midtones have more visible grain)
        weights = (0.5 - np.abs(channel - 0.5)) * 2
        weights = np.clip(weights, 0.05, 0.9)
        
        # Sensitivity mask
        sens_grain = np.clip(sens, 0.4, 0.6)
        
        return noise * weights * sens_grain * real_grain_size

    def _reinhard_tonemap(self, img: np.ndarray, gamma: float) -> np.ndarray:
        # Reinhard Extended: x / (x + white_point)
        # Simple: x / (1 + x)
        # Ensure non-negative to avoid NaNs in power
        mapped = np.maximum(img, 0) / (1.0 + np.maximum(img, 0))
        # Gamma encode to sRGB for display
        return np.power(mapped, 1.0 / gamma) 

    def _aces_fitted_tonemap(self, x: np.ndarray) -> np.ndarray:
        """
        Narkowicz ACES Fitted Tone Mapping.
        Standard approximation used in game engines (e.g. UE4).
        Formula: x(a*x + b) / (x(c*x + d) + e)
        """
        # Ensure non-negative
        x = np.maximum(x, 0)
        
        # Narkowicz Constants
        a = 2.51
        b = 0.03
        c = 2.43
        d = 0.59
        e = 0.14
        
        # Apply curve
        result = (x * (a * x + b)) / (x * (c * x + d) + e)
        
        # Clamp to [0, 1]
        result = np.clip(result, 0.0, 1.0)
        
        # Gamma encode to sRGB for display
        return np.power(result, 1.0 / 2.2)

    def _apply_crosstalk(self, r: np.ndarray, g: np.ndarray, b: np.ndarray, crosstalk: List[float]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        模拟减色法混合 (Subtractive Mixing) 和染料串扰 (Dye Crosstalk).
        原理：
        1. 胶片不记录光，只记录“密度” (Density)。
        2. 将线性光转换为密度：D = -log(E).
        3. 这一层形成的染料会吸收其他波段的光（串扰）。 D_final = Matrix * D_layer.
        4. 转回透过率：T = 10^-D.
        """
        # Avoid log(0)
        epsilon = 1e-6
        
        # 1. Convert to Density (Pseudo-density, assuming simple D-logE relation)
        # We assume input r,g,b are linear 'exposures' or 'transmittances' of the ideal layers
        # Let's treat them as Transmittance => D = -log(T)
        d_r = -np.log10(np.maximum(r, epsilon))
        d_g = -np.log10(np.maximum(g, epsilon))
        d_b = -np.log10(np.maximum(b, epsilon))
        
        # 2. Apply Matrix
        m = crosstalk
        # Matrix layout: [rr, rg, rb, gr, gg, gb, br, bg, bb]
        # D_r_out = D_r * rr + D_g * rg + D_b * rb
        d_r_out = d_r * m[0] + d_g * m[1] + d_b * m[2]
        d_g_out = d_r * m[3] + d_g * m[4] + d_b * m[5]
        d_b_out = d_r * m[6] + d_g * m[7] + d_b * m[8]
        
        # 3. Convert back to Transmittance (Linear Light)
        out_r = np.power(10, -d_r_out)
        out_g = np.power(10, -d_g_out)
        out_b = np.power(10, -d_b_out)
        
        return out_r, out_g, out_b

    def process(self, image: np.ndarray, iso: int = 400, tone_style: str = "filmic", exposure_ev: float = 0.0, halation_intensity: float = 1.0) -> np.ndarray:
        # 1. Linearize
        img_linear = self._to_linear_float(image)
        
        # Apply Exposure Compensation (in linear space, 2^EV)
        if exposure_ev != 0.0:
            img_linear = img_linear * (2.0 ** exposure_ev)

        # 2. Separation
        lux_r, lux_g, lux_b, lux_total = self._calculate_luminance(img_linear)
        
        # 3. Global Sensitivity (Exposure estimation)
        # In linear space, mean can be very low.
        avg_lux = np.mean(lux_total)
        # Adapt sensitivity based on exposure (Auto Exposure compensation simplified)
        exposure_comp = 0.18 / (avg_lux + 1e-4)
        sens = np.clip(1.0, 0.1, 2.0) # Fixed sens for now, logic needs tuning for Linear
        
        params = self.preset
        
        # 4. Bloom (Pyramid)
        # Bloom strength depends on preset and user slider
        bloom_strength = params.sens_factor * 1.5 * halation_intensity
        
        if params.type == "color":
            # Bloom on channels
            # Usually bloom is white (scattering of all light), but in film layers, 
            # red light scatters in red layer etc.
            # Simplified: Bloom the channels independently.
            
            # Use Pyramid Bloom with Wavelength-dependent Radius
            bloom_r = GaussianPyramid.render_bloom(lux_r, bloom_strength, params.red_layer.radius_mult)
            bloom_g = GaussianPyramid.render_bloom(lux_g, bloom_strength, params.green_layer.radius_mult)
            bloom_b = GaussianPyramid.render_bloom(lux_b, bloom_strength, params.blue_layer.radius_mult)
            
            # 5. Composite
            # Linear Additive Model:
            # Result = Direct Light + Scattered Light (Bloom)
            
            res_r = lux_r * params.red_layer.direct + bloom_r * params.red_layer.scatter
            res_g = lux_g * params.green_layer.direct + bloom_g * params.green_layer.scatter
            res_b = lux_b * params.blue_layer.direct + bloom_b * params.blue_layer.scatter
            
            # Apply Subtractive CMY Mixing (Crosstalk)
            # This simulates the physical interaction of dyes where density accumulation is non-linear
            res_r, res_g, res_b = self._apply_crosstalk(res_r, res_g, res_b, params.crosstalk)
            
            # 6. Grain
            # Grain is added to density usually, here we modulate intensity
            grain_r = self._apply_grain(res_r, params.red_layer.grain, 1.0, iso)
            grain_g = self._apply_grain(res_g, params.green_layer.grain, 1.0, iso)
            grain_b = self._apply_grain(res_b, params.blue_layer.grain, 1.0, iso)
            
            res_r = res_r + grain_r
            res_g = res_g + grain_g
            res_b = res_b + grain_b
            
            # 7. Tone Mapping (Linear -> sRGB Display)
            if tone_style == "filmic":
                final_r = self._aces_fitted_tonemap(res_r)
                final_g = self._aces_fitted_tonemap(res_g)
                final_b = self._aces_fitted_tonemap(res_b)
            else:
                final_r = self._reinhard_tonemap(res_r, params.curve.gamma)
                final_g = self._reinhard_tonemap(res_g, params.curve.gamma)
                final_b = self._reinhard_tonemap(res_b, params.curve.gamma)
                
            return cv2.merge([
                np.clip(final_r * 255, 0, 255).astype(np.uint8),
                np.clip(final_g * 255, 0, 255).astype(np.uint8),
                np.clip(final_b * 255, 0, 255).astype(np.uint8)
            ])

        else:
            # B&W Pipeline
            bloom = GaussianPyramid.render_bloom(lux_total, bloom_strength)
            
            res_total = lux_total * params.pan_layer.direct + bloom * params.pan_layer.scatter
            
            grain = self._apply_grain(res_total, params.pan_layer.grain, 1.0, iso)
            res_total = res_total + grain
            
            if tone_style == "filmic":
                final = self._aces_fitted_tonemap(res_total)
            else:
                final = self._reinhard_tonemap(res_total, params.curve.gamma)
                
            return np.clip(final * 255, 0, 255).astype(np.uint8)
