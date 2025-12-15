# 更新日志 (Changelog)

## [1.0.0] - 2024-12-16 (Phos_refactor 物理光学重构版)

Phos_refactor 进行了核心重构，尽量实现真正的“线性光学”模拟流程。

### ✨以此更新的新功能

#### 1. 线性光学工作流 (Linear Optical Workflow)
*   **原生 RAW 支持**: 集成 `rawpy`，直接读取 `.ARW`, `.CR2`, `.NEF`, `.DNG` 等格式的 16-bit 线性光数据 (Gamma=1.0)，绕过非线性的 sRGB 曲线。
*   **32-bit 浮点管线**: 核心引擎现在运行在 HDR 浮点空间 (float32)，完整保留超越人眼可见范围的高光信息。
*   **线性曝光控制**: 新增“曝光补偿”滑块，在线性空间中进行符合物理规律的 ($2^{EV}$) 曝光调整。

#### 2. 高级物理模拟 (Advanced Physical Simulation)
*   **金字塔光晕 (Pyramid Bloom)**: 替代了简单的高斯模糊，使用多尺度金字塔算法来模拟真实的光线在胶片乳剂层中的散射。
*   **红光溢出 (Red Halation/Anti-Halation Layer)**: 实现了基于波长的光线散射。红光的散射半径比蓝光更远，从而在强光源周围产生逼真的橙红色光晕。
*   **CMY 减色混合 (Subtractive CMY Mixing)**: 引入“染料串扰矩阵 (Dye Crosstalk Matrix)”，模拟青、品红、黄染料的非线性吸收特性，带来更深沉、有“厚度”的色彩。
*   **ACES 标准色调映射 (ACES Standard Tone Mapping)**: 使用工业标准的 **Narkowicz ACES Fitted Curve** 替代了原有的近似曲线，确保将在 sRGB 显示器上呈现出电影级的色彩渲染。

#### 3. 扩展胶片库 (Expanded Film Library)
基于厂商技术白皮书 (Datasheets) 校准的历史胶片预设：
*   **Kodak Tri-X 400 (1954)**: 经典的黑白纪实胶片，高反差。
*   **Kodachrome 64 (1974)**: 传奇的彩色反转片，拥有深邃的黑色和鲜艳的红色。
*   **Kodak Vision3 250D (2000s)**: 现代好莱坞电影工业标准，极高的宽容度和独特的光晕。
*   **Kodak Portra 400 & Fuji Pro 400H**: 经过数据校准的专业彩色负片。

#### 4. 专业级控制
*   **ISO 感光度**: 用物理定义的 ISO 滑块 (50-3200) 替代了“颗粒风格”选项，根据密度动态计算颗粒大小。
*   **光晕强度**: 用户可自定义抗光晕层 (Anti-Halation) 的强度。

### 🛠 技术变更
*   **重构**: 将单文件脚本拆分为模块化包 (`phos.core`, `phos.config`, `phos.utils`)。
*   **优化**: 使用金字塔算法优化了大分辨率图片的处理性能。
*   **配置**: 所有的物理参数现在都通过 `FilmPreset` 数据类公开，便于扩展。

---

## [0.1.1] - Legacy
*   最初的概念验证 (Proof-of-concept) 版本。
