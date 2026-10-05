/**
 * 界面自定义功能模块
 * 
 * 提供丰富的界面自定义功能，包括：
 * - 拖拽式布局编辑
 * - 组件大小调整
 * - 位置锁定
 * - 层级管理
 * - 响应式布局设置
 * - 主题切换
 * - 颜色方案定制
 * - 字体样式调整
 * - 动画效果设置
 * - 操作历史记录与撤销/重做
 * - 自定义CSS注入
 * - 配置保存与导出
 */

// 自定义配置管理
const CustomizationManager = {
    // 当前配置
    config: {
        theme: 'light',
        layout: 'default',
        fontSize: 14,
        sidebarLeftVisible: true,
        sidebarRightVisible: true,
        headerVisible: true,
        footerVisible: true,
        compactMode: false,
        customCSS: '',
        animationsEnabled: true,
        transparencyEffects: true,
        // 编辑模式状态
        editMode: false,
        // 拖拽与布局配置
        draggable: true,
        resizable: true,
        responsive: true,
        // 组件配置
        components: {
            header: {
                locked: false,
                zIndex: 100,
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100%',
                height: '60px'
            },
            sidebarLeft: {
                locked: false,
                zIndex: 90,
                position: 'fixed',
                top: '60px',
                left: 0,
                width: '280px',
                height: 'calc(100vh - 60px)'
            },
            sidebarRight: {
                locked: false,
                zIndex: 90,
                position: 'fixed',
                top: '60px',
                right: 0,
                width: '280px',
                height: 'calc(100vh - 60px)'
            },
            chatArea: {
                locked: false,
                zIndex: 80,
                position: 'relative',
                minHeight: '500px'
            },
            footer: {
                locked: false,
                zIndex: 100,
                position: 'fixed',
                bottom: 0,
                left: 0,
                width: '100%',
                height: '40px'
            }
        },
        // 响应式配置
        responsive: {
            breakpoints: {
                sm: 576,
                md: 768,
                lg: 992,
                xl: 1200
            },
            layouts: {
                sm: 'compact',
                md: 'default',
                lg: 'default',
                xl: 'wide'
            }
        },
        // 操作历史
        history: {
            actions: [],
            currentIndex: -1,
            maxHistory: 50
        },
        // 颜色方案
        colorScheme: {
            primary: '#4a90e2',
            secondary: '#6c757d',
            success: '#28a745',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8',
            light: '#f8f9fa',
            dark: '#343a40',
            background: '#ffffff',
            text: '#212529',
            border: '#dee2e6'
        },
        // 字体配置
        font: {
            family: '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            size: {
                base: 14,
                small: 12,
                large: 16,
                xlarge: 18,
                xxlarge: 20
            }
        }
    },
    
    // 预设主题
    themes: {
        light: {
            name: '浅色主题',
            description: '经典的浅色界面，适合日间使用',
            colors: {
                primary: '#4a90e2',
                background: '#ffffff',
                text: '#212529'
            }
        },
        dark: {
            name: '深色主题',
            description: '护眼的深色界面，适合夜间使用',
            colors: {
                primary: '#5a9fd4',
                background: '#1a1a2e',
                text: '#eaeaea'
            }
        },
        blue: {
            name: '蓝色主题',
            description: '清新的蓝色调界面',
            colors: {
                primary: '#2196f3',
                background: '#e3f2fd',
                text: '#1565c0'
            }
        },
        green: {
            name: '绿色主题',
            description: '自然的绿色调界面',
            colors: {
                primary: '#4caf50',
                background: '#e8f5e8',
                text: '#2e7d32'
            }
        },
        purple: {
            name: '紫色主题',
            description: '优雅的紫色调界面',
            colors: {
                primary: '#9c27b0',
                background: '#f3e5f5',
                text: '#6a1b9a'
            }
        },
        orange: {
            name: '橙色主题',
            description: '活力的橙色调界面',
            colors: {
                primary: '#ff9800',
                background: '#fff3e0',
                text: '#e65100'
            }
        },
        pink: {
            name: '粉色主题',
            description: '温馨的粉色调界面',
            colors: {
                primary: '#e91e63',
                background: '#fce4ec',
                text: '#c2185b'
            }
        },
        highContrast: {
            name: '高对比度',
            description: '高对比度主题，适合视力障碍用户',
            colors: {
                primary: '#000000',
                background: '#ffffff',
                text: '#000000'
            }
        }
    },
    
    // 预设布局
    layouts: {
        default: {
            name: '默认布局',
            description: '经典的左右侧边栏布局',
            config: {
                sidebarLeftVisible: true,
                sidebarRightVisible: true,
                sidebarLeftWidth: '280px',
                sidebarRightWidth: '280px'
            }
        },
        compact: {
            name: '紧凑布局',
            description: '更紧凑的界面，显示更多内容',
            config: {
                sidebarLeftVisible: true,
                sidebarRightVisible: false,
                sidebarLeftWidth: '240px',
                sidebarRightWidth: '0'
            }
        },
        wide: {
            name: '宽屏布局',
            description: '最大化聊天区域',
            config: {
                sidebarLeftVisible: false,
                sidebarRightVisible: false,
                sidebarLeftWidth: '0',
                sidebarRightWidth: '0'
            }
        },
        focus: {
            name: '专注模式',
            description: '隐藏所有干扰元素，专注对话',
            config: {
                sidebarLeftVisible: false,
                sidebarRightVisible: false,
                headerVisible: true,
                footerVisible: false,
                sidebarLeftWidth: '0',
                sidebarRightWidth: '0'
            }
        }
    },
    
    /**
     * 初始化自定义管理器
     */
    init() {
        this.loadConfig();
        this.createCustomizerPanel();
        this.bindEvents();
        this.initResponsiveLayout();
        this.applyConfig();
        // 初始状态下确保所有元素不可拖拽
        this.removeDraggableHandlers();
        console.log('自定义管理器已初始化');
    },
    
    /**
     * 加载配置
     */
    loadConfig() {
        const saved = localStorage.getItem('customizationConfig');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                this.config = { ...this.config, ...parsed };
            } catch (e) {
                console.error('加载自定义配置失败:', e);
            }
        }
    },
    
    /**
     * 保存配置
     */
    saveConfig() {
        localStorage.setItem('customizationConfig', JSON.stringify(this.config));
    },
    
    /**
     * 应用配置
     */
    applyConfig() {
        // 应用主题
        this.applyTheme(this.config.theme);
        
        // 应用布局
        this.applyLayout(this.config.layout);
        
        // 应用字体大小
        this.applyFontSize(this.config.fontSize);
        
        // 应用元素可见性
        this.applyElementVisibility();
        
        // 应用自定义CSS
        this.applyCustomCSS();
        
        // 应用动画设置
        this.applyAnimationSettings();
    },
    
    /**
     * 应用主题
     */
    applyTheme(themeName) {
        // 移除所有主题类
        document.body.classList.forEach(cls => {
            if (cls.startsWith('theme-')) {
                document.body.classList.remove(cls);
            }
        });
        
        // 添加新主题
        document.body.classList.add(`theme-${themeName}`);
        this.config.theme = themeName;
        
        // 更新主题选择器
        const themeSelect = document.getElementById('customizer-theme');
        if (themeSelect) {
            themeSelect.value = themeName;
        }
        
        // 触发主题变更事件
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: themeName } }));
    },
    
    /**
     * 应用布局
     */
    applyLayout(layoutName) {
        const layout = this.layouts[layoutName];
        if (!layout) return;
        
        // 移除所有布局类
        document.body.classList.forEach(cls => {
            if (cls.startsWith('layout-')) {
                document.body.classList.remove(cls);
            }
        });
        
        // 添加新布局
        document.body.classList.add(`layout-${layoutName}`);
        this.config.layout = layoutName;
        
        // 应用布局配置
        const config = layout.config;
        
        // 设置侧边栏宽度
        const sidebarLeft = document.getElementById('sidebar-left');
        const sidebarRight = document.getElementById('sidebar-right');
        
        if (sidebarLeft) {
            sidebarLeft.style.width = config.sidebarLeftWidth;
            sidebarLeft.style.display = config.sidebarLeftVisible ? 'block' : 'none';
        }
        
        if (sidebarRight) {
            sidebarRight.style.width = config.sidebarRightWidth;
            sidebarRight.style.display = config.sidebarRightVisible ? 'block' : 'none';
        }
        
        // 设置头部和底部
        const header = document.querySelector('.header');
        const footer = document.querySelector('.footer');
        
        if (header) {
            header.style.display = config.headerVisible !== false ? 'flex' : 'none';
        }
        
        if (footer) {
            footer.style.display = config.footerVisible !== false ? 'flex' : 'none';
        }
        
        // 更新布局选择器
        const layoutSelect = document.getElementById('customizer-layout');
        if (layoutSelect) {
            layoutSelect.value = layoutName;
        }
        
        // 触发布局变更事件
        window.dispatchEvent(new CustomEvent('layoutChanged', { detail: { layout: layoutName } }));
    },
    
    /**
     * 应用字体大小
     */
    applyFontSize(size) {
        document.documentElement.style.setProperty('--font-size-base', `${size}px`);
        this.config.fontSize = size;
        
        // 更新字体大小滑块
        const fontSizeSlider = document.getElementById('customizer-font-size');
        const fontSizeValue = document.getElementById('customizer-font-size-value');
        if (fontSizeSlider) {
            fontSizeSlider.value = size;
        }
        if (fontSizeValue) {
            fontSizeValue.textContent = `${size}px`;
        }
    },
    
    /**
     * 应用元素可见性
     */
    applyElementVisibility() {
        const elements = {
            'sidebar-left': this.config.sidebarLeftVisible,
            'sidebar-right': this.config.sidebarRightVisible,
            'header': this.config.headerVisible,
            'footer': this.config.footerVisible
        };
        
        Object.entries(elements).forEach(([id, visible]) => {
            const element = id === 'header' 
                ? document.querySelector('.header')
                : id === 'footer'
                    ? document.querySelector('.footer')
                    : document.getElementById(id);
            
            if (element) {
                element.style.display = visible ? '' : 'none';
            }
            
            // 更新复选框
            const checkbox = document.getElementById(`customizer-show-${id.replace('-', '-')}`);
            if (checkbox) {
                checkbox.checked = visible;
            }
        });
    },
    
    /**
     * 应用自定义CSS
     */
    applyCustomCSS() {
        let styleElement = document.getElementById('custom-user-css');
        
        if (!styleElement) {
            styleElement = document.createElement('style');
            styleElement.id = 'custom-user-css';
            document.head.appendChild(styleElement);
        }
        
        styleElement.textContent = this.config.customCSS;
        
        // 更新CSS编辑器
        const cssEditor = document.getElementById('customizer-css');
        if (cssEditor && cssEditor.value !== this.config.customCSS) {
            cssEditor.value = this.config.customCSS;
        }
    },
    
    /**
     * 应用动画设置
     */
    applyAnimationSettings() {
        if (this.config.animationsEnabled) {
            document.body.classList.remove('no-animations');
        } else {
            document.body.classList.add('no-animations');
        }
        
        // 更新复选框
        const checkbox = document.getElementById('customizer-animations');
        if (checkbox) {
            checkbox.checked = this.config.animationsEnabled;
        }
    },
    
    /**
     * 创建自定义面板
     */
    createCustomizerPanel() {
        // 检查是否已存在
        if (document.getElementById('customizer-panel')) {
            return;
        }
        
        const panel = document.createElement('div');
        panel.id = 'customizer-panel';
        panel.className = 'customizer-panel';
        panel.innerHTML = `
            <div class="customizer-header">
                <h3>界面自定义</h3>
                <button class="customizer-close" title="关闭">&times;</button>
            </div>
            <div class="customizer-content">
                <!-- 主题选择 -->
                <div class="customizer-section">
                    <h4>主题</h4>
                    <select id="customizer-theme" class="customizer-select">
                        ${Object.entries(this.themes).map(([key, theme]) => 
                            `<option value="${key}">${theme.name}</option>`
                        ).join('')}
                    </select>
                    <p class="customizer-description" id="theme-description">
                        ${this.themes[this.config.theme]?.description || ''}
                    </p>
                </div>
                
                <!-- 布局选择 -->
                <div class="customizer-section">
                    <h4>布局</h4>
                    <select id="customizer-layout" class="customizer-select">
                        ${Object.entries(this.layouts).map(([key, layout]) => 
                            `<option value="${key}">${layout.name}</option>`
                        ).join('')}
                    </select>
                    <p class="customizer-description" id="layout-description">
                        ${this.layouts[this.config.layout]?.description || ''}
                    </p>
                </div>
                
                <!-- 拖拽与调整 -->
                <div class="customizer-section">
                    <h4>拖拽与调整</h4>
                    <label class="customizer-checkbox">
                        <input type="checkbox" id="customizer-draggable" 
                               ${this.config.draggable ? 'checked' : ''}>
                        启用拖拽
                    </label>
                    <label class="customizer-checkbox">
                        <input type="checkbox" id="customizer-resizable" 
                               ${this.config.resizable ? 'checked' : ''}>
                        启用大小调整
                    </label>
                    <label class="customizer-checkbox">
                        <input type="checkbox" id="customizer-responsive" 
                               ${this.config.responsive ? 'checked' : ''}>
                        启用响应式布局
                    </label>
                </div>
                
                <!-- 组件管理 -->
                <div class="customizer-section">
                    <h4>组件管理</h4>
                    <div class="component-controls">
                        ${Object.entries(this.config.components).map(([component, config]) => `
                            <div class="component-control-item">
                                <div class="component-header">
                                    <span>${component}</span>
                                    <label class="customizer-checkbox small">
                                        <input type="checkbox" id="customizer-lock-${component}" 
                                               ${config.locked ? 'checked' : ''}>
                                        锁定
                                    </label>
                                </div>
                                <div class="component-actions">
                                    <button class="customizer-btn tiny" id="customizer-zindex-up-${component}" title="层级上移">↑</button>
                                    <button class="customizer-btn tiny" id="customizer-zindex-down-${component}" title="层级下移">↓</button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- 字体设置 -->
                <div class="customizer-section">
                    <h4>字体设置</h4>
                    <div class="setting-group">
                        <label>字体家族</label>
                        <select id="customizer-font-family" class="customizer-select">
                            <option value='"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif' ${this.config.font.family === '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif' ? 'selected' : ''}>默认字体</option>
                            <option value='"Times New Roman", Times, serif' ${this.config.font.family === '"Times New Roman", Times, serif' ? 'selected' : ''}>Times New Roman</option>
                            <option value='"Courier New", Courier, monospace' ${this.config.font.family === '"Courier New", Courier, monospace' ? 'selected' : ''}>Courier New</option>
                            <option value='"Arial", sans-serif' ${this.config.font.family === '"Arial", sans-serif' ? 'selected' : ''}>Arial</option>
                        </select>
                    </div>
                    <div class="setting-group">
                        <label>基础字体大小</label>
                        <div class="customizer-slider-group">
                            <input type="range" id="customizer-font-size" 
                                   min="12" max="20" value="${this.config.font.size.base}" 
                                   class="customizer-slider">
                            <span id="customizer-font-size-value">${this.config.font.size.base}px</span>
                        </div>
                    </div>
                </div>
                
                <!-- 颜色方案 -->
                <div class="customizer-section">
                    <h4>颜色方案</h4>
                    ${Object.entries(this.config.colorScheme).map(([key, value]) => `
                        <div class="color-picker-group">
                            <label>${key}</label>
                            <div class="color-picker-row">
                                <input type="color" id="customizer-color-${key}" 
                                       value="${value}" class="color-picker">
                                <input type="text" id="customizer-color-text-${key}" 
                                       value="${value}" class="color-text">
                            </div>
                        </div>
                    `).join('')}
                    <button id="customizer-apply-colors" class="customizer-btn">应用颜色</button>
                </div>
                
                <!-- 元素可见性 -->
                <div class="customizer-section">
                    <h4>显示/隐藏元素</h4>
                    <label class="customizer-checkbox">
                        <input type="checkbox" id="customizer-show-sidebar-left" 
                               ${this.config.sidebarLeftVisible ? 'checked' : ''}>
                        左侧功能面板
                    </label>
                    <label class="customizer-checkbox">
                        <input type="checkbox" id="customizer-show-sidebar-right" 
                               ${this.config.sidebarRightVisible ? 'checked' : ''}>
                        右侧面板
                    </label>
                    <label class="customizer-checkbox">
                        <input type="checkbox" id="customizer-show-header" 
                               ${this.config.headerVisible ? 'checked' : ''}>
                        顶部导航栏
                    </label>
                    <label class="customizer-checkbox">
                        <input type="checkbox" id="customizer-show-footer" 
                               ${this.config.footerVisible ? 'checked' : ''}>
                        底部状态栏
                    </label>
                </div>
                
                <!-- 动画设置 -->
                <div class="customizer-section">
                    <h4>动画效果</h4>
                    <label class="customizer-checkbox">
                        <input type="checkbox" id="customizer-animations" 
                               ${this.config.animationsEnabled ? 'checked' : ''}>
                        启用动画效果
                    </label>
                </div>
                
                <!-- 操作历史 -->
                <div class="customizer-section">
                    <h4>操作历史</h4>
                    <div class="history-actions">
                        <button id="customizer-undo" class="customizer-btn" title="撤销">撤销</button>
                        <button id="customizer-redo" class="customizer-btn" title="重做">重做</button>
                    </div>
                </div>
                
                <!-- 自定义CSS -->
                <div class="customizer-section">
                    <h4>自定义CSS</h4>
                    <textarea id="customizer-css" class="customizer-textarea" 
                              placeholder="输入自定义CSS代码...">${this.config.customCSS}</textarea>
                    <button id="customizer-apply-css" class="customizer-btn">应用CSS</button>
                </div>
                
                <!-- 操作按钮 -->
                <div class="customizer-actions">
                    <button id="customizer-reset" class="customizer-btn secondary">重置</button>
                    <button id="customizer-export" class="customizer-btn">导出配置</button>
                    <button id="customizer-import" class="customizer-btn">导入配置</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
        
        // 添加样式
        this.addCustomizerStyles();
    },
    
    /**
     * 添加自定义面板样式
     */
    addCustomizerStyles() {
        if (document.getElementById('customizer-styles')) {
            return;
        }
        
        const styles = document.createElement('style');
        styles.id = 'customizer-styles';
        styles.textContent = `
            .customizer-panel {
                position: fixed;
                right: -400px;
                top: 60px;
                width: 380px;
                height: calc(100vh - 60px);
                background: var(--bg-primary);
                border-left: 1px solid var(--border-color);
                box-shadow: -2px 0 10px rgba(0,0,0,0.1);
                z-index: 1000;
                transition: right 0.3s ease;
                display: flex;
                flex-direction: column;
            }
            
            .customizer-panel.open {
                right: 0;
            }
            
            .customizer-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                border-bottom: 1px solid var(--border-color);
                background: var(--bg-secondary);
            }
            
            .customizer-header h3 {
                margin: 0;
                font-size: 18px;
                color: var(--text-primary);
            }
            
            .customizer-close {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: var(--text-secondary);
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                transition: all 0.2s;
            }
            
            .customizer-close:hover {
                background: var(--bg-tertiary);
                color: var(--text-primary);
            }
            
            .customizer-content {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
            }
            
            .customizer-section {
                margin-bottom: 25px;
            }
            
            .customizer-section h4 {
                margin: 0 0 12px 0;
                font-size: 14px;
                color: var(--text-primary);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .customizer-select {
                width: 100%;
                padding: 10px;
                border: 1px solid var(--border-color);
                border-radius: 6px;
                background: var(--bg-primary);
                color: var(--text-primary);
                font-size: 14px;
                cursor: pointer;
            }
            
            .customizer-description {
                margin: 8px 0 0 0;
                font-size: 12px;
                color: var(--text-secondary);
            }
            
            .customizer-slider-group {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .customizer-slider {
                flex: 1;
                height: 6px;
                border-radius: 3px;
                background: var(--bg-tertiary);
                outline: none;
                -webkit-appearance: none;
            }
            
            .customizer-slider::-webkit-slider-thumb {
                -webkit-appearance: none;
                width: 18px;
                height: 18px;
                border-radius: 50%;
                background: var(--primary-color);
                cursor: pointer;
            }
            
            .customizer-checkbox {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 8px 0;
                cursor: pointer;
                font-size: 14px;
                color: var(--text-primary);
            }
            
            .customizer-checkbox input[type="checkbox"] {
                width: 18px;
                height: 18px;
                cursor: pointer;
            }
            
            .customizer-textarea {
                width: 100%;
                min-height: 120px;
                padding: 10px;
                border: 1px solid var(--border-color);
                border-radius: 6px;
                background: var(--bg-primary);
                color: var(--text-primary);
                font-family: monospace;
                font-size: 12px;
                resize: vertical;
            }
            
            .customizer-btn {
                padding: 10px 20px;
                margin-top: 10px;
                background: var(--primary-color);
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.2s;
            }
            
            .customizer-btn:hover {
                opacity: 0.9;
            }
            
            .customizer-btn.secondary {
                background: var(--bg-tertiary);
                color: var(--text-primary);
            }
            
            .customizer-actions {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                padding-top: 20px;
                border-top: 1px solid var(--border-color);
            }
            
            .customizer-actions .customizer-btn {
                flex: 1;
                min-width: 100px;
                margin-top: 0;
            }
            
            /* 组件控制 */
            .component-controls {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .component-control-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px;
                background: var(--bg-secondary);
                border-radius: 6px;
            }
            
            .component-header {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .component-actions {
                display: flex;
                gap: 5px;
            }
            
            .customizer-btn.tiny {
                padding: 4px 8px;
                font-size: 12px;
                min-width: auto;
            }
            
            .customizer-checkbox.small {
                font-size: 12px;
            }
            
            /* 颜色选择器 */
            .color-picker-group {
                margin-bottom: 10px;
            }
            
            .color-picker-row {
                display: flex;
                gap: 10px;
                align-items: center;
            }
            
            .color-picker {
                width: 40px;
                height: 30px;
                border: 1px solid var(--border-color);
                border-radius: 4px;
                cursor: pointer;
            }
            
            .color-text {
                flex: 1;
                padding: 6px 10px;
                border: 1px solid var(--border-color);
                border-radius: 4px;
                background: var(--bg-primary);
                color: var(--text-primary);
                font-size: 12px;
                font-family: monospace;
            }
            
            /* 历史操作 */
            .history-actions {
                display: flex;
                gap: 10px;
            }
            
            /* 切换按钮 */
            .customizer-toggle {
                position: fixed;
                right: 20px;
                bottom: 80px;
                width: 50px;
                height: 50px;
                border-radius: 50%;
                background: var(--primary-color);
                color: white;
                border: none;
                cursor: pointer;
                font-size: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                z-index: 999;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .customizer-toggle:hover {
                transform: scale(1.1);
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }
            
            /* 调整器样式 */
            .resizer {
                position: absolute;
                width: 10px;
                height: 100%;
                right: 0;
                top: 0;
                cursor: col-resize;
                background: rgba(74, 144, 226, 0.2);
                z-index: 10;
            }
            
            .resizer:hover {
                background: rgba(74, 144, 226, 0.4);
            }
            
            /* 无动画模式 */
            body.no-animations * {
                animation: none !important;
                transition: none !important;
            }
            
            /* 编辑模式样式 */
            body.edit-mode {
                cursor: crosshair;
            }
            
            /* 可编辑区域高亮 */
            .editable-area {
                border: 2px dashed #4a90e2 !important;
                box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
                transition: all 0.2s ease;
            }
            
            .editable-area:hover {
                border-color: #357abd !important;
                box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.3) !important;
            }
            
            /* 拖拽状态 */
            .editable-area.dragging {
                opacity: 0.8;
                z-index: 1000 !important;
            }
            
            /* 响应式调整 */
            @media (max-width: 768px) {
                .customizer-panel {
                    width: 100%;
                    right: -100%;
                }
                
                .color-picker-row {
                    flex-direction: column;
                    align-items: stretch;
                }
                
                .color-picker {
                    width: 100%;
                }
            }
        `;
        
        document.head.appendChild(styles);
        
        // 添加切换按钮
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'customizer-toggle';
        toggleBtn.innerHTML = '🎨';
        toggleBtn.title = '界面自定义';
        toggleBtn.onclick = () => this.togglePanel();
        document.body.appendChild(toggleBtn);
    },
    
    /**
     * 切换面板显示
     */
    togglePanel() {
        const panel = document.getElementById('customizer-panel');
        if (panel) {
            const isOpen = panel.classList.toggle('open');
            if (isOpen) {
                this.enterEditMode();
            } else {
                this.exitEditMode();
            }
        }
    },
    
    /**
     * 进入编辑模式
     */
    enterEditMode() {
        this.config.editMode = true;
        document.body.classList.add('edit-mode');
        this.initDragAndDrop();
        this.initResize();
        this.highlightEditableAreas();
        this.showNotification('进入编辑模式');
    },
    
    /**
     * 退出编辑模式
     */
    exitEditMode() {
        this.config.editMode = false;
        document.body.classList.remove('edit-mode');
        this.removeDraggableHandlers();
        this.removeResizableHandlers();
        this.removeHighlights();
        this.showNotification('退出编辑模式');
    },
    
    /**
     * 高亮可编辑区域
     */
    highlightEditableAreas() {
        const editableElements = [
            '.header',
            '#sidebar-left',
            '#sidebar-right',
            '.chat-area',
            '.footer'
        ];
        
        editableElements.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                element.classList.add('editable-area');
            }
        });
    },
    
    /**
     * 移除高亮
     */
    removeHighlights() {
        const editableElements = document.querySelectorAll('.editable-area');
        editableElements.forEach(element => {
            element.classList.remove('editable-area');
        });
    },
    
    /**
     * 移除拖拽处理器
     */
    removeDraggableHandlers() {
        const draggableElements = {
            header: '.header',
            'sidebar-left': '#sidebar-left',
            'sidebar-right': '#sidebar-right',
            'chat-area': '.chat-area',
            footer: '.footer'
        };
        
        Object.entries(draggableElements).forEach(([component, selector]) => {
            const element = document.querySelector(selector);
            if (element) {
                // 移除所有事件监听器
                const newElement = element.cloneNode(true);
                element.parentNode.replaceChild(newElement, element);
                
                // 恢复默认样式
                newElement.style.cursor = '';
                newElement.style.position = 'fixed';
                newElement.style.left = `${this.config.components[component].left || 0}px`;
                newElement.style.top = `${this.config.components[component].top || 0}px`;
                newElement.style.zIndex = this.config.components[component].zIndex;
            }
        });
    },
    
    /**
     * 移除大小调整处理器
     */
    removeResizableHandlers() {
        const resizers = document.querySelectorAll('.resizer');
        resizers.forEach(resizer => {
            resizer.remove();
        });
    },
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 点击页面其他区域关闭编辑模式
        document.addEventListener('click', (e) => {
            const panel = document.getElementById('customizer-panel');
            const toggleBtn = document.querySelector('.customizer-toggle');
            const isPanelOpen = panel && panel.classList.contains('open');
            const isClickInsidePanel = panel && panel.contains(e.target);
            const isClickOnToggle = toggleBtn && toggleBtn.contains(e.target);
            const isClickOnFunctionBtn = e.target.closest('.function-btn');
            
            // 如果点击的是功能按钮，不关闭面板
            if (isPanelOpen && !isClickInsidePanel && !isClickOnToggle && !isClickOnFunctionBtn) {
                this.togglePanel();
            }
        });
        
        // 主题选择
        const themeSelect = document.getElementById('customizer-theme');
        if (themeSelect) {
            themeSelect.addEventListener('change', (e) => {
                this.applyTheme(e.target.value);
                this.saveConfig();
                
                // 更新描述
                const desc = document.getElementById('theme-description');
                if (desc) {
                    desc.textContent = this.themes[e.target.value]?.description || '';
                }
            });
        }
        
        // 布局选择
        const layoutSelect = document.getElementById('customizer-layout');
        if (layoutSelect) {
            layoutSelect.addEventListener('change', (e) => {
                this.applyLayout(e.target.value);
                this.saveConfig();
                
                // 更新描述
                const desc = document.getElementById('layout-description');
                if (desc) {
                    desc.textContent = this.layouts[e.target.value]?.description || '';
                }
            });
        }
        
        // 拖拽与调整设置
        const draggableCheckbox = document.getElementById('customizer-draggable');
        if (draggableCheckbox) {
            draggableCheckbox.addEventListener('change', (e) => {
                this.config.draggable = e.target.checked;
                this.saveConfig();
                this.showNotification(`拖拽已${e.target.checked ? '启用' : '禁用'}`);
            });
        }
        
        const resizableCheckbox = document.getElementById('customizer-resizable');
        if (resizableCheckbox) {
            resizableCheckbox.addEventListener('change', (e) => {
                this.config.resizable = e.target.checked;
                this.saveConfig();
                this.showNotification(`大小调整已${e.target.checked ? '启用' : '禁用'}`);
            });
        }
        
        const responsiveCheckbox = document.getElementById('customizer-responsive');
        if (responsiveCheckbox) {
            responsiveCheckbox.addEventListener('change', (e) => {
                this.config.responsive = e.target.checked;
                this.saveConfig();
                this.showNotification(`响应式布局已${e.target.checked ? '启用' : '禁用'}`);
            });
        }
        
        // 组件锁定
        Object.entries(this.config.components).forEach(([component]) => {
            const lockCheckbox = document.getElementById(`customizer-lock-${component}`);
            if (lockCheckbox) {
                lockCheckbox.addEventListener('change', (e) => {
                    this.config.components[component].locked = e.target.checked;
                    this.saveConfig();
                    this.showNotification(`${component} 已${e.target.checked ? '锁定' : '解锁'}`);
                });
            }
            
            // 层级调整
            const zIndexUpBtn = document.getElementById(`customizer-zindex-up-${component}`);
            if (zIndexUpBtn) {
                zIndexUpBtn.addEventListener('click', () => {
                    this.adjustComponentZIndex(component, 'up');
                });
            }
            
            const zIndexDownBtn = document.getElementById(`customizer-zindex-down-${component}`);
            if (zIndexDownBtn) {
                zIndexDownBtn.addEventListener('click', () => {
                    this.adjustComponentZIndex(component, 'down');
                });
            }
        });
        
        // 字体设置
        const fontFamilySelect = document.getElementById('customizer-font-family');
        if (fontFamilySelect) {
            fontFamilySelect.addEventListener('change', (e) => {
                this.config.font.family = e.target.value;
                this.applyFont();
                this.saveConfig();
                this.showNotification('字体家族已更新');
            });
        }
        
        const fontSizeSlider = document.getElementById('customizer-font-size');
        if (fontSizeSlider) {
            fontSizeSlider.addEventListener('input', (e) => {
                const size = parseInt(e.target.value);
                this.config.font.size.base = size;
                this.applyFont();
                
                const sizeValue = document.getElementById('customizer-font-size-value');
                if (sizeValue) {
                    sizeValue.textContent = `${size}px`;
                }
            });
            
            fontSizeSlider.addEventListener('change', () => {
                this.saveConfig();
                this.showNotification('字体大小已更新');
            });
        }
        
        // 颜色方案
        const applyColorsBtn = document.getElementById('customizer-apply-colors');
        if (applyColorsBtn) {
            applyColorsBtn.addEventListener('click', () => {
                const colors = {};
                Object.keys(this.config.colorScheme).forEach(key => {
                    const colorInput = document.getElementById(`customizer-color-${key}`);
                    if (colorInput) {
                        colors[key] = colorInput.value;
                    }
                });
                this.customizeColorScheme(colors);
            });
        }
        
        // 颜色输入同步
        Object.keys(this.config.colorScheme).forEach(key => {
            const colorInput = document.getElementById(`customizer-color-${key}`);
            const textInput = document.getElementById(`customizer-color-text-${key}`);
            
            if (colorInput && textInput) {
                colorInput.addEventListener('input', (e) => {
                    textInput.value = e.target.value;
                });
                
                textInput.addEventListener('input', (e) => {
                    if (/^#[0-9A-Fa-f]{6}$/.test(e.target.value)) {
                        colorInput.value = e.target.value;
                    }
                });
            }
        });
        
        // 元素可见性
        const visibilityElements = [
            { id: 'customizer-show-sidebar-left', config: 'sidebarLeftVisible' },
            { id: 'customizer-show-sidebar-right', config: 'sidebarRightVisible' },
            { id: 'customizer-show-header', config: 'headerVisible' },
            { id: 'customizer-show-footer', config: 'footerVisible' }
        ];
        
        visibilityElements.forEach(({ id, config }) => {
            const checkbox = document.getElementById(id);
            if (checkbox) {
                checkbox.addEventListener('change', (e) => {
                    this.config[config] = e.target.checked;
                    this.applyElementVisibility();
                    this.saveConfig();
                });
            }
        });
        
        // 动画设置
        const animationsCheckbox = document.getElementById('customizer-animations');
        if (animationsCheckbox) {
            animationsCheckbox.addEventListener('change', (e) => {
                this.config.animationsEnabled = e.target.checked;
                this.applyAnimationSettings();
                this.saveConfig();
            });
        }
        
        // 操作历史
        const undoBtn = document.getElementById('customizer-undo');
        if (undoBtn) {
            undoBtn.addEventListener('click', () => this.undo());
        }
        
        const redoBtn = document.getElementById('customizer-redo');
        if (redoBtn) {
            redoBtn.addEventListener('click', () => this.redo());
        }
        
        // 自定义CSS
        const applyCSSBtn = document.getElementById('customizer-apply-css');
        if (applyCSSBtn) {
            applyCSSBtn.addEventListener('click', () => {
                const cssEditor = document.getElementById('customizer-css');
                if (cssEditor) {
                    this.config.customCSS = cssEditor.value;
                    this.applyCustomCSS();
                    this.saveConfig();
                    this.showNotification('CSS已应用');
                }
            });
        }
        
        // 关闭按钮
        const closeBtn = document.querySelector('.customizer-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.togglePanel());
        }
        
        // 重置按钮
        const resetBtn = document.getElementById('customizer-reset');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetConfig());
        }
        
        // 导出按钮
        const exportBtn = document.getElementById('customizer-export');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportConfig());
        }
        
        // 导入按钮
        const importBtn = document.getElementById('customizer-import');
        if (importBtn) {
            importBtn.addEventListener('click', () => this.importConfig());
        }
    },
    
    /**
     * 重置配置
     */
    resetConfig() {
        if (confirm('确定要重置所有自定义设置吗？')) {
            this.config = {
                theme: 'light',
                layout: 'default',
                fontSize: 14,
                sidebarLeftVisible: true,
                sidebarRightVisible: true,
                headerVisible: true,
                footerVisible: true,
                compactMode: false,
                customCSS: '',
                animationsEnabled: true,
                transparencyEffects: true,
                // 拖拽与布局配置
                draggable: true,
                resizable: true,
                responsive: true,
                // 组件配置
                components: {
                    header: {
                        locked: false,
                        zIndex: 100,
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '60px'
                    },
                    sidebarLeft: {
                        locked: false,
                        zIndex: 90,
                        position: 'fixed',
                        top: '60px',
                        left: 0,
                        width: '280px',
                        height: 'calc(100vh - 60px)'
                    },
                    sidebarRight: {
                        locked: false,
                        zIndex: 90,
                        position: 'fixed',
                        top: '60px',
                        right: 0,
                        width: '280px',
                        height: 'calc(100vh - 60px)'
                    },
                    chatArea: {
                        locked: false,
                        zIndex: 80,
                        position: 'relative',
                        minHeight: '500px'
                    },
                    footer: {
                        locked: false,
                        zIndex: 100,
                        position: 'fixed',
                        bottom: 0,
                        left: 0,
                        width: '100%',
                        height: '40px'
                    }
                },
                // 响应式配置
                responsive: {
                    breakpoints: {
                        sm: 576,
                        md: 768,
                        lg: 992,
                        xl: 1200
                    },
                    layouts: {
                        sm: 'compact',
                        md: 'default',
                        lg: 'default',
                        xl: 'wide'
                    }
                },
                // 操作历史
                history: {
                    actions: [],
                    currentIndex: -1,
                    maxHistory: 50
                },
                // 颜色方案
                colorScheme: {
                    primary: '#4a90e2',
                    secondary: '#6c757d',
                    success: '#28a745',
                    danger: '#dc3545',
                    warning: '#ffc107',
                    info: '#17a2b8',
                    light: '#f8f9fa',
                    dark: '#343a40',
                    background: '#ffffff',
                    text: '#212529',
                    border: '#dee2e6'
                },
                // 字体配置
                font: {
                    family: '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                    size: {
                        base: 14,
                        small: 12,
                        large: 16,
                        xlarge: 18,
                        xxlarge: 20
                    }
                }
            };
            
            this.applyConfig();
            this.saveConfig();
            this.showNotification('设置已重置');
        }
    },
    
    /**
     * 导出配置
     */
    exportConfig() {
        const configData = JSON.stringify(this.config, null, 2);
        const blob = new Blob([configData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'customization-config.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        this.showNotification('配置已导出');
    },
    
    /**
     * 导入配置
     */
    importConfig() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = (event) => {
                try {
                    const imported = JSON.parse(event.target.result);
                    this.config = { ...this.config, ...imported };
                    this.applyConfig();
                    this.saveConfig();
                    this.showNotification('配置已导入');
                } catch (err) {
                    alert('导入失败：无效的配置文件');
                }
            };
            reader.readAsText(file);
        };
        
        input.click();
    },
    
    /**
     * 显示通知
     */
    showNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: var(--success-color);
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 10001;
            animation: slideInRight 0.3s ease;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    },
    
    /**
     * 初始化拖拽功能
     */
    initDragAndDrop() {
        if (!this.config.draggable || !this.config.editMode) return;
        
        const draggableElements = {
            header: '.header',
            'sidebar-left': '#sidebar-left',
            'sidebar-right': '#sidebar-right',
            'chat-area': '.chat-area',
            footer: '.footer'
        };
        
        Object.entries(draggableElements).forEach(([component, selector]) => {
            const element = document.querySelector(selector);
            if (element) {
                this.makeDraggable(element, component);
            }
        });
    },
    
    /**
     * 使元素可拖拽
     */
    makeDraggable(element, component) {
        let isDragging = false;
        let startX, startY, startLeft, startTop;
        
        // 确保元素是固定定位
        element.style.position = 'fixed';
        // 在编辑模式下显示拖拽光标
        element.style.cursor = 'move';
        
        // 鼠标按下事件
        const handleMouseDown = (e) => {
            if (this.config.components[component].locked || !this.config.editMode) return;
            
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            startLeft = parseInt(element.style.left) || 0;
            startTop = parseInt(element.style.top) || 0;
            element.style.zIndex = this.config.components[component].zIndex + 10;
            element.style.userSelect = 'none';
            element.classList.add('dragging');
        };
        
        // 鼠标移动事件
        const handleMouseMove = (e) => {
            if (!isDragging || !this.config.editMode) return;
            
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;
            
            const newLeft = startLeft + deltaX;
            const newTop = startTop + deltaY;
            
            element.style.left = `${newLeft}px`;
            element.style.top = `${newTop}px`;
        };
        
        // 鼠标释放事件
        const handleMouseUp = () => {
            if (isDragging) {
                isDragging = false;
                element.style.zIndex = this.config.components[component].zIndex;
                element.style.userSelect = '';
                element.classList.remove('dragging');
                
                // 更新配置
                this.config.components[component].left = parseInt(element.style.left) || 0;
                this.config.components[component].top = parseInt(element.style.top) || 0;
                
                // 记录操作
                this.addToHistory('drag', { component, position: { left: this.config.components[component].left, top: this.config.components[component].top } });
                
                this.saveConfig();
            }
        };
        
        // 添加事件监听器
        element.addEventListener('mousedown', handleMouseDown);
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        
        // 保存事件监听器引用，以便后续移除
        element._dragListeners = {
            mousedown: handleMouseDown,
            mousemove: handleMouseMove,
            mouseup: handleMouseUp
        };
    },
    
    /**
     * 初始化大小调整功能
     */
    initResize() {
        if (!this.config.resizable || !this.config.editMode) return;
        
        const resizableElements = {
            'sidebar-left': '#sidebar-left',
            'sidebar-right': '#sidebar-right',
            'chat-area': '.chat-area'
        };
        
        Object.entries(resizableElements).forEach(([component, selector]) => {
            const element = document.querySelector(selector);
            if (element) {
                this.makeResizable(element, component);
            }
        });
    },
    
    /**
     * 使元素可调整大小
     */
    makeResizable(element, component) {
        const resizer = document.createElement('div');
        resizer.className = 'resizer';
        resizer.style.cssText = `
            position: absolute;
            width: 10px;
            height: 100%;
            right: 0;
            top: 0;
            cursor: col-resize;
            background: rgba(74, 144, 226, 0.2);
            z-index: 10;
        `;
        
        element.style.position = 'relative';
        element.appendChild(resizer);
        
        let isResizing = false;
        let startX, startWidth;
        
        resizer.addEventListener('mousedown', (e) => {
            if (this.config.components[component].locked || !this.config.editMode) return;
            
            isResizing = true;
            startX = e.clientX;
            startWidth = element.offsetWidth;
            document.body.style.userSelect = 'none';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isResizing || !this.config.editMode) return;
            
            const deltaX = e.clientX - startX;
            const newWidth = Math.max(200, startWidth + deltaX);
            
            element.style.width = `${newWidth}px`;
        });
        
        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.userSelect = '';
                
                // 更新配置
                this.config.components[component].width = element.offsetWidth;
                
                // 记录操作
                this.addToHistory('resize', { component, size: { width: this.config.components[component].width } });
                
                this.saveConfig();
            }
        });
    },
    
    /**
     * 初始化响应式布局
     */
    initResponsiveLayout() {
        if (!this.config.responsive) return;
        
        const checkResponsive = () => {
            const width = window.innerWidth;
            let currentLayout = 'default';
            
            if (width < this.config.responsive.breakpoints.sm) {
                currentLayout = this.config.responsive.layouts.sm;
            } else if (width < this.config.responsive.breakpoints.md) {
                currentLayout = this.config.responsive.layouts.md;
            } else if (width < this.config.responsive.breakpoints.lg) {
                currentLayout = this.config.responsive.layouts.lg;
            } else {
                currentLayout = this.config.responsive.layouts.xl;
            }
            
            if (this.config.layout !== currentLayout) {
                this.applyLayout(currentLayout);
                this.saveConfig();
            }
        };
        
        // 初始检查
        checkResponsive();
        
        // 窗口大小变化时检查
        window.addEventListener('resize', checkResponsive);
    },
    
    /**
     * 锁定/解锁组件
     */
    toggleComponentLock(component) {
        if (this.config.components[component]) {
            this.config.components[component].locked = !this.config.components[component].locked;
            this.saveConfig();
            this.showNotification(`${component} 已${this.config.components[component].locked ? '锁定' : '解锁'}`);
        }
    },
    
    /**
     * 调整组件层级
     */
    adjustComponentZIndex(component, direction) {
        if (this.config.components[component]) {
            const currentZIndex = this.config.components[component].zIndex;
            const newZIndex = direction === 'up' ? currentZIndex + 10 : Math.max(10, currentZIndex - 10);
            
            this.config.components[component].zIndex = newZIndex;
            
            const element = document.querySelector(this.getComponentSelector(component));
            if (element) {
                element.style.zIndex = newZIndex;
            }
            
            this.addToHistory('zindex', { component, zIndex: newZIndex });
            this.saveConfig();
            this.showNotification(`${component} 层级已调整`);
        }
    },
    
    /**
     * 获取组件选择器
     */
    getComponentSelector(component) {
        const selectors = {
            header: '.header',
            'sidebar-left': '#sidebar-left',
            'sidebar-right': '#sidebar-right',
            'chat-area': '.chat-area',
            footer: '.footer'
        };
        return selectors[component] || '';
    },
    
    /**
     * 添加操作到历史记录
     */
    addToHistory(actionType, data) {
        const action = {
            type: actionType,
            data: data,
            timestamp: Date.now()
        };
        
        // 截断历史记录
        if (this.config.history.currentIndex < this.config.history.actions.length - 1) {
            this.config.history.actions = this.config.history.actions.slice(0, this.config.history.currentIndex + 1);
        }
        
        // 添加新操作
        this.config.history.actions.push(action);
        
        // 限制历史记录长度
        if (this.config.history.actions.length > this.config.history.maxHistory) {
            this.config.history.actions.shift();
        } else {
            this.config.history.currentIndex++;
        }
    },
    
    /**
     * 撤销操作
     */
    undo() {
        if (this.config.history.currentIndex >= 0) {
            const action = this.config.history.actions[this.config.history.currentIndex];
            this.config.history.currentIndex--;
            this.undoAction(action);
            this.showNotification('已撤销操作');
        }
    },
    
    /**
     * 重做操作
     */
    redo() {
        if (this.config.history.currentIndex < this.config.history.actions.length - 1) {
            this.config.history.currentIndex++;
            const action = this.config.history.actions[this.config.history.currentIndex];
            this.redoAction(action);
            this.showNotification('已重做操作');
        }
    },
    
    /**
     * 撤销操作
     */
    undoAction(action) {
        // 这里需要根据操作类型实现撤销逻辑
        console.log('撤销操作:', action);
    },
    
    /**
     * 重做操作
     */
    redoAction(action) {
        // 这里需要根据操作类型实现重做逻辑
        console.log('重做操作:', action);
    },
    
    /**
     * 定制颜色方案
     */
    customizeColorScheme(colors) {
        Object.assign(this.config.colorScheme, colors);
        this.applyColorScheme();
        this.saveConfig();
        this.showNotification('颜色方案已更新');
    },
    
    /**
     * 应用颜色方案
     */
    applyColorScheme() {
        const colors = this.config.colorScheme;
        
        // 设置CSS变量
        Object.entries(colors).forEach(([key, value]) => {
            document.documentElement.style.setProperty(`--${key}-color`, value);
        });
    },
    
    /**
     * 定制字体
     */
    customizeFont(fontConfig) {
        Object.assign(this.config.font, fontConfig);
        this.applyFont();
        this.saveConfig();
        this.showNotification('字体设置已更新');
    },
    
    /**
     * 应用字体设置
     */
    applyFont() {
        const font = this.config.font;
        document.documentElement.style.setProperty('--font-family', font.family);
        document.documentElement.style.setProperty('--font-size-base', `${font.size.base}px`);
        document.documentElement.style.setProperty('--font-size-small', `${font.size.small}px`);
        document.documentElement.style.setProperty('--font-size-large', `${font.size.large}px`);
        document.documentElement.style.setProperty('--font-size-xlarge', `${font.size.xlarge}px`);
        document.documentElement.style.setProperty('--font-size-xxlarge', `${font.size.xxlarge}px`);
    }
};

// 添加动画样式
const animationStyles = document.createElement('style');
animationStyles.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(animationStyles);

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    CustomizationManager.init();
});

// 暴露全局接口
window.CustomizationManager = CustomizationManager;
