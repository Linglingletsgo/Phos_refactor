# Phos_refactor v1.0.0 - 基于计算光学的胶片模拟 (Physically Based Film Simulation)

**Phos_refactor** 是一个基于“计算光学”概念的胶片模拟引擎（基于项目 Phos）。与传统的滤镜不同，Phos_refactor 计算光线在胶片层上的物理行为，复现模拟摄影自然、柔美且立体的质感。

**Phos_refactor** is a film simulation engine based on the concept of "Computational Optics" (formerly Phos). Unlike traditional filters, it calculates the physical behavior of light on film layers.

> **v1.0.0 重大更新**: 现已支持真正的 **线性光学工作流 (Linear Optical Workflow)**、**ACES 标准色调映射** 以及 **物理染料耦合模拟**。

> [!WARNING]
> **AI 生成声明 (AI Generation Disclaimer)**
> 本项目在重构过程中大规模使用了 AI 辅助编程。由于代码量较大，部分 AI 生成的逻辑、注释或物理参数可能包含幻觉或不准确信息，且暂未经过完全的人工验证。使用时请自行甄别。
> This project was refactored with extensive use of AI coding assistance. Due to the scale, some AI-generated code, comments, or physical parameters may contain hallucinations or inaccuracies that have not been fully manually verified.

> [!NOTE]
> **项目目的 (Project Purpose)**
> 本项目的主要目的是**提供一些可能可行的思路**，探索计算光学在胶片模拟领域的应用潜力，而非作为成熟的商业软件产品。希望能够抛砖引玉，为社区带来更多灵感。
> The primary purpose of this project is to **provide some potentially feasible ideas**, exploring the potential of computational optics in film simulation, rather than serving as a mature commercial product. We hope to inspire further innovation in the community.


## ✨ 核心特性 Key Features (v1.0.0)

1.  **真正的线性工作流 (True Linear Workflow)**:
    *   直接支持 **RAW 文件** (`.ARW`, `.CR2`, `.DNG`, etc.)。
    *   在 32-bit 线性浮点空间 (Gamma=1.0) 处理图像数据，确保物理准确性。
    *   **曝光补偿**: 基于物理的方式恢复高光和阴影细节。

2.  **高级物理模拟 (Advanced Physical Simulation)**:
    *   **金字塔光晕 (Pyramid Bloom)**: 模拟光线在乳剂层中的物理散射。
    *   **红光溢出 (Red Halation)**: 基于波长的散射模拟（红光散射更远），产生逼真的橙红光晕。
    *   **CMY 减色混合**: 模拟青、品红、黄染料的化学相互作用。

3.  **扩展胶片库 (Expanded Film Library)**:
    *   **Kodak Portra 400** & **Fuji Pro 400H** (数据校准).
    *   **Kodachrome 64** (复古正片).
    *   **Kodak Vision3 250D** (现代电影).
    *   **Kodak Tri-X 400** (经典黑白).

4.  **专业标准 (Professional Standards)**:
    *   **ACES Standard Tone Mapping**: 工业标准的电影级色彩渲染。
    *   **ISO Ratings**: 基于 ISO 速度的物理颗粒模拟。

## 🚀 使用方法 Usage

```bash
pip install -r requirements.txt
streamlit run main.py
```

## 📦 依赖 Requirements

*   Python 3.10+
*   **rawpy** (新增! 用于 RAW 处理)
*   numpy
*   opencv-python-headless
*   streamlit
*   pillow

# 许可证 License

本项目基于 AGPL-3.0 许可证分发。
This project is licensed under AGPL-3.0.

本项目包含了由 **@LYCO6273** 开发的原始代码。
This project contains original code developed by **@LYCO6273**.

**Dominic Duan** 对本项目进行了重构与功能扩展。
**Dominic Duan** refactored and extended this project.

根据 AGPL-3.0 条款，您可以：
- 自由使用、研究、修改源代码
- 用于个人或商业项目（必须开源）

您必须：
- **保留原作者及重构作者的版权声明**
- **在相同许可证 (AGPL-3.0) 下分发您的修改版本**

# 作者 Author

## 重构与更新 (Refactoring & Update)
**@Dominic Duan**
*   **GitHub**: [https://github.com/Linglingletsgo/Phos_refactor](https://github.com/Linglingletsgo/Phos_refactor)
*   **Website**: [www.dominicduan.com](http://www.dominicduan.com)
*   **Email**: lingonthebeat@gmail.com
*   **小红书 (XiaoHongShu)**: @Linglingletsgo

## 原作者 (Original Author)
**@LYCO6273**
*   **GitHub**: [https://github.com/LYCO6273/Phos](https://github.com/LYCO6273/Phos)
*   **Email**: lyco_p@163.com
