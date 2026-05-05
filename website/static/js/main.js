// 页面切换功能
function showPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.getElementById('page-' + pageName).classList.add('active');
    
    const navMap = {
        'home': '首页',
        'features': '功能',
        'about': '关于我们',
        'help': '帮助',
        'contact': '联系'
    };
    
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.textContent.includes(navMap[pageName])) {
            link.classList.add('active');
        }
    });
    
    window.scrollTo(0, 0);
}

// 侧边栏切换
document.querySelectorAll('.sidebar-item').forEach(item => {
    item.addEventListener('click', function() {
        document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
        this.classList.add('active');
    });
});

// FAQ折叠
function toggleFaq(element) {
    element.classList.toggle('open');
    element.querySelector('.faq-toggle').textContent = element.classList.contains('open') ? '−' : '+';
}

// 滚动动画
const observerOptions = { threshold: 0.1 };
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// 为卡片添加动画
document.querySelectorAll('.feature-card, .testimonial-card, .pricing-card, .help-card, .value-card, .team-card').forEach((el, index) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = `opacity 0.6s ease ${index * 0.05}s, transform 0.6s ease ${index * 0.05}s`;
    observer.observe(el);
});

// 平滑滚动
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// 表单提交
document.querySelectorAll('.form-submit').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        alert('感谢您的留言！我们会尽快与您联系。');
    });
});

// 搜索功能（预留）
function searchHelp() {
    const query = document.getElementById('search-input').value;
    if (query.trim()) {
        alert(`搜索: ${query}`);
    }
}