# 答题助手 - 安卓版

基于 Kivy + KivyMD 开发的安卓答题软件，可打包成 APK 安装到安卓手机。

## 功能清单

- ✅ 四种题型：单选、多选、判断、案例分析
- ✅ 答题模式：计分、计时、随机抽题、错题明细
- ✅ 学习模式：浏览题目、查看答案解析、添加笔记、AI 解析
- ✅ 错题本：错题练习、错误次数统计
- ✅ 题库管理：Excel 导入、题目浏览、科目管理
- ✅ AI 解析：支持 DeepSeek、硅基流动、豆包、智谱 GLM 四个服务，解析时可自由选择
- ✅ 数据互通：通过 Excel 文件与电脑版互导

## 项目结构

```
quiz_app_android/
├── main.py              # 程序入口
├── db.py                # 数据库（已适配安卓路径）
├── ai_helper.py         # AI 解析（多服务支持）
├── file_import.py       # Excel 导入
├── export_module.py     # 导出（Word/PDF/Excel，已适配安卓字体）
├── buildozer.spec       # 打包配置
├── requirements.txt     # Python 依赖
├── ui/
│   ├── home_screen.py     # 首页
│   ├── quiz_screen.py     # 答题界面
│   ├── review_screen.py   # 学习模式
│   ├── wrong_screen.py    # 错题本
│   ├── bank_screen.py     # 题库管理
│   └── settings_screen.py # 设置
└── README.md
```

## 打包成 APK 教程

### 方式一：GitHub Actions 自动打包（最推荐，完全免费）

项目已内置 GitHub Actions 配置，上传代码后自动打包：

1. 注册 GitHub 账号：https://github.com
2. 新建仓库（Repository），名字随意（如 `quiz-app-android`）
3. 把本项目所有文件上传到仓库（直接拖拽上传，或用 git 推送）
4. 上传完成后，点仓库顶部的「**Actions**」标签
5. 会看到一个名为「Build Android APK」的任务正在运行
6. 等待约 30-40 分钟，任务完成后点进去
7. 在页面底部「**Artifacts**」区域下载 `quiz-app-apk.zip`
8. 解压后就是 APK 文件，传到手机安装即可

> 特点：完全不占本地空间，免费，配置一次以后每次更新代码自动打包。

### 方式二：Google Colab 在线打包

（国内访问不太方便，备选）

1. 打开 https://colab.research.google.com/
2. 新建笔记本，依次执行以下命令：

```bash
# 安装 buildozer
!pip install buildozer
!sudo apt update
!sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 上传项目文件到 Colab（左侧文件面板上传 zip）
# 解压项目
!unzip quiz_app_android.zip
%cd quiz_app_android

# 开始打包（第一次需要下载依赖，约20-40分钟）
!buildozer android debug
```

3. 打包完成后，APK 在 `bin/` 目录下，下载到手机安装即可

### 方式二：本地 Linux 打包

需要 Ubuntu/Debian 系统：

```bash
# 安装依赖
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

pip install buildozer cython

# 进入项目目录
cd quiz_app_android

# 打包
buildozer android debug
```

### 打包注意事项

1. **第一次打包很慢**：需要下载 Android SDK、NDK 和 Python 依赖，约 20-40 分钟
2. **APK 位置**：打包成功后在 `bin/QuizApp-1.0.0-arm64-v8a-debug.apk`
3. **安装到手机**：把 APK 传到手机，点击安装（需要允许"未知来源"）
4. **权限**：首次启动会请求存储权限，用于导入导出 Excel 文件

## 手机电脑数据互通

### 电脑 → 手机
1. 电脑版「题库管理」→「导出题库」→ 选择 Excel 格式
2. 将 Excel 文件传到手机（微信/QQ/U盘）
3. 手机版「题库管理」→「导入 Excel」→ 选择文件

### 手机 → 电脑
1. 手机版「题库管理」→「导出题库」→ Excel 格式
2. 将导出的 Excel 文件传到电脑
3. 电脑版「导入题目」→ 选择该 Excel 文件

## AI 解析配置

在「设置」中配置 AI 服务，支持四个平台：

| 平台 | 免费情况 | 模型 |
|------|----------|------|
| DeepSeek | 付费 | deepseek-v4-flash |
| 硅基流动 | 注册送¥14，小模型免费 | Qwen/Qwen2.5-7B-Instruct |
| 豆包 | 新用户送50万tokens | 自定义接入点 |
| 智谱 GLM | GLM-4-Flash 永久免费 | glm-4-flash |

配置后，答题/学习时点「AI 智能解析」可选择用哪个服务。

## Excel 导入格式

| 列名 | 说明 | 必填 |
|------|------|------|
| 题干 | 题目内容 | 是 |
| 题型 | single/multiple/judge/case | 是 |
| 选项A | 选项A内容 | 选择题必填 |
| 选项B | 选项B内容 | 选择题必填 |
| 选项C | 选项C内容 | 否 |
| 选项D | 选项D内容 | 否 |
| 答案 | 正确答案（如 A、ABC、正确、自定义） | 是 |
| 解析 | 答案解析 | 否 |
| 科目 | 科目名称 | 否 |

可在电脑版中下载标准模板。

## 常见问题

**Q：打包失败怎么办？**
A：检查 buildozer.spec 中的配置，确保依赖都正确。第一次打包必须联网。

**Q：安装后闪退？**
A：可能是权限问题，确保授予存储权限。或查看 logcat 日志：`adb logcat | grep python`

**Q：Excel 导入找不到文件？**
A：将 Excel 文件放到手机存储根目录（/sdcard/）或 Download 目录，导入时输入文件名。

**Q：AI 解析超时？**
A：检查网络连接，或在设置中增加超时时间。
