# 打砖块 · BREAKOUT

> 鼠标/方向键移动挡板，反弹小球清砖；发光砖块掉落道具，清空全部砖块进入下一关，球速逐关加快。

用 [Zan](https://github.com/joyspinch/zan-lang) 语言写的独立游戏项目（仓库根自带 git 仓库）。完整设计与实现说明见 [`PROJECT.md`](PROJECT.md)。

## 玩法

- 鼠标/方向键移动挡板，反弹小球清砖
- 发光砖块掉落道具：多球、加长挡板等
- 清空全部砖块进入下一关，球速逐关加快

## 构建

需要 [zan-lang](https://github.com/joyspinch/zan-lang) 仓库（`zanc` 编译器、公共包与 stdlib 都在里面）：

```powershell
git clone https://github.com/joyspinch/zan-lang.git
$env:ZAN_HOME = 'D:/path/to/zan-lang'   # 指到刚克隆的 zan-lang 仓库根

pwsh -File client/tools/build.ps1
```

产物：`build/breakout/Breakout.exe`（运行目录要带上它旁边的 `assets/` 与 `skins/`）。

## 运行

```powershell
cd build/breakout
.\Breakout.exe
```

## 测试

```powershell
pwsh -File client/tools/test.ps1
```

## 目录结构

```
breakout/
client/
  src/      # 游戏源码（.zan 源码 + HTML 界面设计稿）
  assets/   # 位图 / 音频素材
  tests/    # 玩法断言用例
  tools/    # 构建与测试脚本
PROJECT.md
```

## 素材与授权

- **大背景图已改为本地程序化生成**：`client/assets/menu_bg.png` 由仓内 `client/tools/make_bgs.py` 生成（纯 numpy + PIL，无外部素材来源），重新生成命令 `python client/tools/make_bgs.py`。
- **标题图 `title.png` 由图像模型生成**：来自 zan-lang 早期打砖块模板（neon brick-breaker），由图像模型（gpt-image-2）产出，来源见 [zan-lang `60f325c0`](https://github.com/joyspinch/zan-lang/commit/60f325c013315235a28984075e29db7d10420e2d)。注意该图的标题字样是模型生成的形近字（并非规范中文字形），如需准确文字建议另行排版替换。
- 仓库不含任何第三方版权素材；全部位图均为本项目自产（图像模型生成或本地程序化生成）。

## 许可

本仓库采用 [MIT 许可](LICENSE)。依赖的 zan-lang 仓库采用 ZCSL（Zan Community Source License 1.0）。

## 更多文档

- [`PROJECT.md`](PROJECT.md) —— 完整设计与实现说明
- [`client/README.md`](client/README.md) —— 客户端侧说明
