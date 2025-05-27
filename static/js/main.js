/**
 * FIT-Alumni Main JavaScript
 * Xử lý các hiệu ứng và tính năng chung cho toàn bộ ứng dụng
 */

document.addEventListener('DOMContentLoaded', function() {
    // ===== Biến toàn cục =====
    const body = document.body;
    
    // ===== Khởi tạo các thành phần =====
    initTooltips();
    setupScrollToTop();
    setupMobileNavigation();
    setupDarkModeToggle();
    setupNotifications();
    setupFormValidation();
    enhanceDropdowns();
    
    /**
     * Khởi tạo tooltips
     */
    function initTooltips() {
        const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
        if (tooltips.length > 0 && typeof bootstrap !== 'undefined') {
            tooltips.forEach(tooltip => {
                new bootstrap.Tooltip(tooltip);
            });
        }
    }
    
    /**
     * Thiết lập nút cuộn lên đầu trang
     */
    function setupScrollToTop() {
        // Tạo nút cuộn lên đầu trang
        const scrollTopBtn = document.createElement('button');
        scrollTopBtn.classList.add('scroll-to-top');
        scrollTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
        body.appendChild(scrollTopBtn);
        
        // Xử lý hiển thị/ẩn nút khi cuộn
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                scrollTopBtn.classList.add('active');
            } else {
                scrollTopBtn.classList.remove('active');
            }
        });
        
        // Xử lý sự kiện click
        scrollTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    /**
     * Thiết lập điều hướng trên thiết bị di động
     */
    function setupMobileNavigation() {
        const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (mobileMenuToggle && navbarCollapse) {
            mobileMenuToggle.addEventListener('click', function() {
                navbarCollapse.classList.toggle('show');
                this.classList.toggle('active');
                
                // Thêm/xóa lớp no-scroll cho body để ngăn cuộn khi menu mở
                if (navbarCollapse.classList.contains('show')) {
                    body.classList.add('no-scroll');
                } else {
                    body.classList.remove('no-scroll');
                }
            });
            
            // Đóng menu khi click bên ngoài
            document.addEventListener('click', function(event) {
                if (
                    navbarCollapse.classList.contains('show') && 
                    !navbarCollapse.contains(event.target) && 
                    !mobileMenuToggle.contains(event.target)
                ) {
                    navbarCollapse.classList.remove('show');
                    mobileMenuToggle.classList.remove('active');
                    body.classList.remove('no-scroll');
                }
            });
        }
    }
    
    /**
     * Thiết lập chuyển đổi chế độ tối/sáng
     */
    function setupDarkModeToggle() {
        const darkModeToggle = document.querySelector('.dark-mode-toggle');
        
        if (darkModeToggle) {
            // Kiểm tra cài đặt đã lưu
            const isDarkMode = localStorage.getItem('darkMode') === 'true';
            
            // Áp dụng chế độ ban đầu
            if (isDarkMode) {
                body.classList.add('dark-mode');
                darkModeToggle.classList.add('active');
            }
            
            // Xử lý sự kiện click
            darkModeToggle.addEventListener('click', function() {
                body.classList.toggle('dark-mode');
                this.classList.toggle('active');
                
                // Lưu cài đặt
                localStorage.setItem('darkMode', body.classList.contains('dark-mode'));
            });
        }
    }
    
    /**
     * Thiết lập thông báo
     */
    function setupNotifications() {
        const notificationBell = document.querySelector('.notification-bell');
        const notificationDropdown = document.querySelector('.notification-dropdown');
        
        if (notificationBell && notificationDropdown) {
            // Xử lý sự kiện click vào chuông thông báo
            notificationBell.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                notificationDropdown.classList.toggle('show');
                
                // Đánh dấu đã đọc khi mở dropdown
                if (notificationDropdown.classList.contains('show')) {
                    this.classList.remove('has-unread');
                    
                    // Gửi yêu cầu đánh dấu đã đọc đến server (nếu cần)
                    // fetch('/mark-notifications-read', { method: 'POST' });
                }
            });
            
            // Đóng dropdown khi click bên ngoài
            document.addEventListener('click', function(event) {
                if (
                    notificationDropdown.classList.contains('show') && 
                    !notificationDropdown.contains(event.target) && 
                    !notificationBell.contains(event.target)
                ) {
                    notificationDropdown.classList.remove('show');
                }
            });
        }
    }
    
    /**
     * Thiết lập kiểm tra hợp lệ cho các biểu mẫu
     */
    function setupFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');
        
        forms.forEach(form => {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                
                form.classList.add('was-validated');
            });
            
            // Kiểm tra mật khẩu khớp nhau (nếu có)
            const password = form.querySelector('input[name="password"]');
            const confirmPassword = form.querySelector('input[name="confirm_password"]');
            
            if (password && confirmPassword) {
                confirmPassword.addEventListener('input', function() {
                    if (password.value !== this.value) {
                        this.setCustomValidity('Mật khẩu không khớp');
                    } else {
                        this.setCustomValidity('');
                    }
                });
                
                password.addEventListener('input', function() {
                    if (confirmPassword.value && password.value !== confirmPassword.value) {
                        confirmPassword.setCustomValidity('Mật khẩu không khớp');
                    } else {
                        confirmPassword.setCustomValidity('');
                    }
                });
            }
        });
    }
    
    /**
     * Cải thiện các dropdown
     */
    function enhanceDropdowns() {
        const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
        
        dropdownToggles.forEach(toggle => {
            const dropdown = toggle.nextElementSibling;
            
            if (dropdown && dropdown.classList.contains('dropdown-menu')) {
                // Thêm hiệu ứng animation khi mở dropdown
                toggle.addEventListener('click', function(event) {
                    event.preventDefault();
                    event.stopPropagation();
                    
                    if (dropdown.classList.contains('show')) {
                        dropdown.classList.remove('show');
                        dropdown.classList.add('hiding');
                        
                        // Xóa lớp hiding sau khi animation kết thúc
                        setTimeout(() => {
                            dropdown.classList.remove('hiding');
                        }, 300);
                    } else {
                        dropdown.classList.add('showing');
                        dropdown.classList.add('show');
                        
                        // Xóa lớp showing sau khi animation kết thúc
                        setTimeout(() => {
                            dropdown.classList.remove('showing');
                        }, 300);
                    }
                });
                
                // Đóng dropdown khi click bên ngoài
                document.addEventListener('click', function(event) {
                    if (
                        dropdown.classList.contains('show') && 
                        !dropdown.contains(event.target) && 
                        !toggle.contains(event.target)
                    ) {
                        dropdown.classList.remove('show');
                        dropdown.classList.add('hiding');
                        
                        // Xóa lớp hiding sau khi animation kết thúc
                        setTimeout(() => {
                            dropdown.classList.remove('hiding');
                        }, 300);
                    }
                });
            }
        });
    }
}); 