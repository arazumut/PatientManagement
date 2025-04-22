// Toggle Sidebar
const toggleSidebarBtn = document.getElementById('toggle-sidebar');
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');

toggleSidebarBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
    
    // Change icon based on state
    if (sidebar.classList.contains('collapsed')) {
        toggleSidebarBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
    } else {
        toggleSidebarBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
    }
});

// Responsive sidebar toggle for mobile
function handleResponsiveSidebar() {
    if (window.innerWidth <= 992) {
        sidebar.classList.remove('collapsed');
        mainContent.classList.remove('expanded');
    }
}

// Initialize on load
window.addEventListener('load', handleResponsiveSidebar);
window.addEventListener('resize', handleResponsiveSidebar);

// Animate stats cards on scroll
const animateOnScroll = () => {
    const statCards = document.querySelectorAll('.stat-card');
    
    statCards.forEach((card, index) => {
        const cardPosition = card.getBoundingClientRect().top;
        const screenPosition = window.innerHeight / 1.3;
        
        if (cardPosition < screenPosition) {
            card.style.animation = `fadeIn 0.5s ease forwards ${index * 0.1}s`;
        }
    });
};

window.addEventListener('scroll', animateOnScroll);
window.addEventListener('load', animateOnScroll);

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });

    // Form alanlarını form-control sınıfıyla otomatik olarak güncelle
    const formInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="date"], input[type="datetime-local"], input[type="number"], select, textarea');
    
    formInputs.forEach(input => {
        if (!input.classList.contains('form-control')) {
            input.classList.add('form-control');
        }
    });
    
    // Mesajları otomatik kapat
    const alertMessages = document.querySelectorAll('.alert, .error-message');
    
    alertMessages.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 500);
        }, 5000);
    });
    
    // Aktif menü öğesini vurgula
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.menu-item');
    
    menuItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '/') {
            item.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            item.classList.add('active');
        }
    });
    
    // Mobil cihazlarda sidebar davranışı
    const mobileMediaQuery = window.matchMedia('(max-width: 991.98px)');
    
    function handleMobileChange(e) {
        if (e.matches) {
            // Mobil görünüme geçtiğinde sidebar'ı kapat
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
            
            // Sidebar dışına tıklandığında sidebar'ı kapat
            document.addEventListener('click', function(event) {
                if (!sidebar.contains(event.target) && 
                    !toggleSidebarBtn.contains(event.target) && 
                    !sidebar.classList.contains('collapsed')) {
                    sidebar.classList.add('collapsed');
                }
            });
        } else {
            // Masaüstü görünüme geçtiğinde sidebar'ı aç
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
        }
    }
    
    // Sayfa yüklendiğinde ve ekran boyutu değiştiğinde kontrol et
    mobileMediaQuery.addListener(handleMobileChange);
    handleMobileChange(mobileMediaQuery);
    
    // Şifre göster/gizle fonksiyonu
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        // Göz ikonu için container oluştur
        const container = document.createElement('div');
        container.className = 'password-toggle';
        container.innerHTML = '<i class="fas fa-eye"></i>';
        
        // İkonu input alanından sonra yerleştir
        input.parentNode.insertBefore(container, input.nextSibling);
        
        // Icon tıklama olayını dinle
        container.addEventListener('click', function() {
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            
            // İkonu değiştir
            container.innerHTML = type === 'password' ? 
                '<i class="fas fa-eye"></i>' : 
                '<i class="fas fa-eye-slash"></i>';
        });
    });
    
    // Form girişlerinde animasyon efekti
    const animateFormInputs = document.querySelectorAll('.form-control');
    animateFormInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentNode.classList.add('input-focused');
        });
        
        input.addEventListener('blur', function() {
            if (this.value === '') {
                this.parentNode.classList.remove('input-focused');
            }
        });
        
        // Sayfa yüklendiğinde değer varsa sınıfı ekle
        if (input.value !== '') {
            input.parentNode.classList.add('input-focused');
        }
    });
    
    // Özel select stillerini active et
    const customSelects = document.querySelectorAll('select.form-control');
    customSelects.forEach(select => {
        select.addEventListener('change', function() {
            if (this.value) {
                this.classList.add('has-value');
            } else {
                this.classList.remove('has-value');
            }
        });
        
        // Sayfa yüklendiğinde değer varsa sınıfı ekle
        if (select.value) {
            select.classList.add('has-value');
        }
    });
});

// CSS için yeni stiller dinamik olarak ekle
document.addEventListener('DOMContentLoaded', function() {
    // CSS ekleme fonksiyonu
    function addStyle(styles) {
        const css = document.createElement('style');
        css.type = 'text/css';
        css.appendChild(document.createTextNode(styles));
        document.getElementsByTagName('head')[0].appendChild(css);
    }
    
    // Yeni stiller ekle
    const newStyles = `
        .password-toggle {
            position: absolute;
            right: 1rem;
            top: 50%;
            transform: translateY(-50%);
            cursor: pointer;
            color: var(--gray-dark);
            z-index: 2;
        }
        
        .input-with-icon .password-toggle {
            right: 1rem;
        }
        
        .password-toggle:hover {
            color: var(--primary);
        }
        
        .input-focused .form-label {
            color: var(--primary);
        }
        
        .input-focused .form-control {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
            background-color: #fff;
        }
        
        .input-with-icon.input-focused i {
            color: var(--primary);
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        .form-group.has-error .form-control {
            border-color: var(--danger);
            animation: shake 0.4s linear;
        }
        
        .form-group.has-error .form-label {
            color: var(--danger);
        }
        
        .form-group.has-error i {
            color: var(--danger);
        }
        
        .form-control.has-value {
            background-color: #fff;
        }
        
        select.form-control.has-value {
            color: var(--dark);
            font-weight: 500;
        }
    `;
    
    addStyle(newStyles);
    
    // Form hata durumunu kontrol et
    const errorLists = document.querySelectorAll('.errorlist');
    errorLists.forEach(errorList => {
        const formGroup = errorList.closest('.form-group');
        if (formGroup) {
            formGroup.classList.add('has-error');
        }
    });
}); 